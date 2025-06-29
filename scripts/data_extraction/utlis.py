import re
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.mapping_data.classification_data import against_israel_themes, against_israel_keywords
from scripts.data_extraction.constants import TONE_WEIGHTS, THEME_WEIGHT, KEYWORD_WEIGHT, CLASSIFICATION_THRESHOLD, ARTICLES_COLLECTION, EVENTS_COLLECTION, gd, url_to_country
from backend.app.core.database import db



def get_page_title(t):
    r = re.compile("<PAGE_TITLE>(.*)</PAGE_TITLE>")
    try:
        l = r.findall(t)
        if len(l) == 0:
            return None
        return l[0]
    except:
        return None


def get_page_author(t):
    r = re.compile("<PAGE_AUTHORS>(.*)</PAGE_AUTHORS>")
    try:
        l = r.findall(t)
        if len(l) == 0:
            return None
        authors = l[0].split(";")
        # Filter out empty strings and validate author names
        valid_authors = []
        for author in authors:
            if author and re.match(r'^[A-Za-z\s\',-]+$', author.strip()):
                valid_authors.append(author.strip())
        return valid_authors if valid_authors else None
    except:
        return None


def parse_v2tone(tone_string):
    try:
        # Split the comma-separated string into individual values
        tones = tone_string.split(",")
        return {
            "overall": float(tones[0]),
            "positive": float(tones[1]),
            "negative": float(tones[2]),
            "polarity": float(tones[3]),
            "activity": float(tones[4]),
            "emotionality": float(tones[5]),
            "word_count": int(tones[6]),
        }
    except (IndexError, ValueError):
        return None


# Function to extract domain from URL
def extract_domain(url):
    if not url:
        return None

    # Remove protocol if present
    if "://" in url:
        url = url.split("://")[1]

    # Remove path and query parameters
    url = url.split("/")[0]

    # Remove www. if present
    if url.startswith("www."):
        url = url[4:]

    return url

# Function to get country from URL
def get_country_from_url(url, url_to_country, country_code_to_name):
    if not url:
        return None

    domain = extract_domain(url)
    if not domain:
        return None

    # Try to find the country code for the domain
    country_code = url_to_country.get(domain)
    if country_code:
        return country_code_to_name.get(country_code, country_code)

    return None


def contains_keywords(field, keywords):
    if pd.isnull(field):
        return False
    return any(k.lower() in field.lower() for k in keywords)


def extract_gdelt_data(start_date, end_date):
    # Convert to string if datetime object is passed
    if isinstance(start_date, datetime):
        start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(end_date, datetime):
        end_date = end_date.strftime("%Y-%m-%d %H:%M:%S")
        
    results = gd.Search(
        ["{}".format(start_date), "{}".format(end_date)],
        table="gkg",
        coverage=True,
        translation=False,
    )
    return results


def refactor_data_df(results):

    df = results[
        [
            "GKGRECORDID",
            "DATE",
            "SourceCommonName",
            "DocumentIdentifier",
            "V2Themes",
            "V2Locations",
            "V2Persons",
            "V2Organizations",
            "SocialImageEmbeds",
            "SocialVideoEmbeds",
            "V2Tone",
            "Extras",
        ]
    ]

    df["PageTitle"] = df["Extras"].apply(get_page_title)
    df["PageAuthors"] = df["Extras"].apply(get_page_author)
    filtered = df[
        df["PageTitle"].apply(
            lambda x: contains_keywords(
                x,
                [
                    "israel",
                    "israeli",
                    "jews",
                    "jewish",
                    "zionist",
                    "zionism",
                    "gaza",
                    "hamas",
                    "genocide",
                    "war crime",
                    "occupation",
                    "boycott israel",
                    "bds movement",
                    "apartheid",
                    "gaza strip",
                    "gaza war",
                ],
            )
            # or bool(re.search(r"(?i)(anti.?sem|anti.?jew|anti.?zion|gaza.?gen)", str(x)))
        )
    ]
    
    filtered = filtered.copy()

    # Extract title, URL and author
    filtered["PageTitle"] = df["PageTitle"]
    filtered["PageUrl"] = filtered["DocumentIdentifier"]
    filtered["PageAuthors"] = df["PageAuthors"]

    # Get country from URL
    filtered["SourceCountry"] = filtered["SourceCommonName"].apply(lambda x: url_to_country.get(x))

    # Parse V2Tone into components
    filtered["Tones"] = filtered["V2Tone"].apply(parse_v2tone)

    # Convert DATE format (YYYYMMDDHHMMSS) to ISO format using datetime
    filtered["ISODate"] = filtered["DATE"].apply(
        lambda x: datetime.strptime(str(int(x)), "%Y%m%d%H%M%S").isoformat() + "Z"
    )
    filtered["TimePassedDate"] = filtered["DATE"]

    filtered["Themes"] = filtered["V2Themes"].apply(lambda x: None if pd.isna(x) else x)

    result_df = filtered.rename(columns={"GKGRECORDID": "OriginalGdeltId"})
    # Select and rename columns as requested
    result_df = result_df[
        [
            "ISODate",
            "TimePassedDate",
            "Themes",
            "Tones",
            "PageTitle",
            "PageUrl",
            "SourceCountry",
            "OriginalGdeltId",
            "PageAuthors",
        ]
    ]

    return result_df


def create_mongo_docs(result_df):
    # Convert DataFrame to list of dictionaries for MongoDB
    mongo_docs = []
    for _, row in result_df.iterrows():
        doc = {
            "date": {"isoDate": row["ISODate"], "timePassedDate": row["TimePassedDate"]},
            "themes": row["Themes"],
            "tones": row["Tones"],
            "pageTitle": row["PageTitle"],
            "pageUrl": row["PageUrl"],
            "sourceCountry": row["SourceCountry"],
            "originalGdeltId": row["OriginalGdeltId"],
            "pageAuthors": row["PageAuthors"],
        }
        mongo_docs.append(doc)
    return mongo_docs


def create_save_docs_event(results_length, end_date, is_success):
    doc = {
        "eventType": "save_docs",
        "isSuccess": is_success,
        "articlesAmount": results_length,
        "eventTime": end_date,
    }
    return [doc]


def insert_to_mongo(mongo_record, db, collection_name):
    try:
        if db == "":
            # Write to file if db is empty string
            with open(f"{collection_name}.json", "w") as f:
                json.dump(mongo_record, f)
            is_inserted = True
        else:
            collection = db[collection_name]
            collection.insert_many(mongo_record)
            is_inserted = True
    except Exception as e:
        print(f"Error inserting records: {str(e)}")
        is_inserted = False

    return is_inserted


def get_latest_event_time(db):
    try:
        if db == "":
            # Read from file if db is empty string
            with open("events.json", "r") as f:
                events = json.load(f)
            latest_event = max(events, key=lambda x: x["eventTime"])
        else:
            collection = db[EVENTS_COLLECTION]
            latest_event = collection.find_one({"eventType": "save_docs"}, sort=[("eventTime", -1)])
        if latest_event:
            return datetime.fromisoformat(latest_event["eventTime"].replace("Z", "+00:00"))
        return None
    except Exception as e:
        print(f"Error getting latest event time: {str(e)}")
        return None


def compute_sentiment_score(tones: Dict[str, float]) -> float:
    """
    Computes a weighted score based on tone values.
    Higher score = higher likelihood of negative bias toward Israel.
    Score is normalized between 0 and 10.

    Parameters:
        tones (dict): Dictionary containing tone metrics like 'overall', 'positive', 'negative', etc.

    Returns:
        float: Normalized weighted sentiment score between 0 and 10
    """
    score = 0.0
    for key, weight in TONE_WEIGHTS.items():
        value = tones.get(key, 0.0)
        score += value * weight

    # Normalize score to 0-10 range
    # Assuming max possible score is 20 (based on weights)
    normalized_score = min(max(score, 0), 20) / 2
    return normalized_score


def extract_theme_ids(theme_str: str) -> List[str]:
    """
    Extracts theme tags (like CRISISLEX_xxx, WB_yyy) from a long theme string.

    Parameters:
        theme_str (str): Raw themes string from article

    Returns:
        List[str]: List of normalized theme codes
    """
    if not theme_str:
        return []
    return re.findall(r"[A-Z_]+", theme_str)


def theme_score(theme_str: str, against_themes: List[str]) -> float:
    """
    Scores the article based on matching themes that are considered anti-Israel.
    Score is normalized between 0 and 10.

    Parameters:
        theme_str (str): Raw themes string from article
        against_themes (list): List of themes considered 'against Israel'

    Returns:
        float: Normalized score based on theme matches between 0 and 10
    """
    themes = extract_theme_ids(theme_str)
    hits = sum(1 for theme in themes if theme in against_themes)
    raw_score = hits * THEME_WEIGHT

    # Normalize score to 0-10 range
    # Assuming max possible themes is 5
    normalized_score = min(hits, 5) * 2
    return normalized_score


def keyword_score(text: str, keywords: List[str]) -> float:
    """
    Scores the article based on the presence of specific anti-Israel keywords.
    Score is normalized between 0 and 10.

    Parameters:
        text (str): Combined page title and URL
        keywords (list): List of keywords considered 'against Israel'

    Returns:
        float: Normalized score based on keyword matches between 0 and 10
    """
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    raw_score = hits * KEYWORD_WEIGHT

    # Normalize score to 0-10 range
    # Assuming max possible keywords is 5
    normalized_score = min(hits, 5) * 2
    return normalized_score


def classify_article(text: str, tones: Dict[str, float], theme_str: str) -> bool:
    """
    Combines tone score, theme score, and keyword score to classify the article.
    All scores are normalized between 0 and 10, with a total possible score of 30.

    Parameters:
        text (str): Article's title + URL
        tones (dict): Tone scores
        theme_str (str): Themes string

    Returns:
        bool: True if article is suspected to be against Israel (isAgainstIsrael = True)
    """
    # Get normalized scores (0-10 each)
    tone_score = compute_sentiment_score(tones)
    theme_score_val = theme_score(theme_str, against_israel_themes)
    keyword_score_val = keyword_score(text, against_israel_keywords)

    # Calculate final score (0-30 range)
    final_score = tone_score + theme_score_val + keyword_score_val

    # Normalize to 0-10 range
    normalized_final_score = final_score / 3

    return normalized_final_score >= CLASSIFICATION_THRESHOLD


def filter_articles(articles):
    return [article for article in articles if article['pageAuthors'] != None and article['sourceCountry'] != None]

def extract_classified_articles(start_date, end_date):
    
    print(f"Extracting data from {start_date} to {end_date}")

    try:
        gdelt_data = extract_gdelt_data(start_date, end_date)
        refactored_gdelt_data = refactor_data_df(gdelt_data)
        print(f"Found {len(refactored_gdelt_data)} matching articles")

        if len(refactored_gdelt_data) > 0:
            articles_json = create_mongo_docs(refactored_gdelt_data)
            articles = filter_articles(articles_json)
            for article in articles:
                classification = classify_article(article["pageTitle"], article["tones"], article["themes"])
                article["isAgainstIsrael"] = classification

            is_inserted = insert_to_mongo(articles, db, ARTICLES_COLLECTION)
            save_docs_event = create_save_docs_event(len(articles), end_date, is_inserted)
            insert_to_mongo(save_docs_event, db, EVENTS_COLLECTION)
            if is_inserted:
                print(f"Inserted {len(articles)} documents into MongoDB")
            else:
                print("Failed to insert documents into MongoDB")

            print(f"Saved data to mongodb")

    except Exception as e:
        print(f"Error processing data for {start_date}: {str(e)}")

"""
This function is used to extract data per day, for a range of dates.
Date is an object of type datetime, where the format is YYYY-MM-DD HH:MM:SS
"""
def per_day_extraction(start, end):

    print(f"Starting extraction from {start} to {end}")

    # Loop through each day
    current_date = start
    while current_date < end:
        start_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
        next_date = current_date + timedelta(days=1)
        end_date = min(next_date, end).strftime("%Y-%m-%d %H:%M:%S")

        extract_classified_articles(start_date, end_date)

        current_date = next_date