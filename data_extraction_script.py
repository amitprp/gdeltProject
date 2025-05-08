import gdelt
from datetime import datetime
import re
import pandas as pd
import os
import json
from pymongo import MongoClient
from datetime import datetime, timedelta


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
        return authors if authors != [""] else None
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


# Function to load URL to country mapping
def load_url_to_country_mapping(file_path):
    url_to_country = {}
    country_code_to_name = {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    domain = parts[0].strip()
                    country_code = parts[1].strip()
                    country_name = parts[2].strip()

                    url_to_country[domain] = country_code
                    country_code_to_name[country_code] = country_name

    except Exception as e:
        print(f"Error loading URL to country mapping: {e}")

    return url_to_country, country_code_to_name


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
        return "Unknown"

    domain = extract_domain(url)
    if not domain:
        return "Unknown"

    # Try to find the country code for the domain
    country_code = url_to_country.get(domain)
    if country_code:
        return country_code_to_name.get(country_code, country_code)

    return "Unknown"


def contains_keywords(field, keywords):
    if pd.isnull(field):
        return False
    return any(k.lower() in field.lower() for k in keywords)


def extract_gdelt_data(gd, start_date, end_date):

    start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
    end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
    results = gd.Search(
        ["{}".format(start_date), "{}".format(end_date)],
        table="gkg",
        coverage=True,
        translation=False,
    )
    return results


def refactor_data_df(results, url_to_country):

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
        collection = db[collection_name]
        collection.insert_many(mongo_record)
        is_inserted = True
    except:
        is_inserted = False

    return is_inserted


def get_latest_event_time(db):
    try:
        collection = db["events"]
        latest_event = collection.find_one({"eventType": "save_docs"}, sort=[("eventTime", -1)])
        if latest_event:
            return datetime.fromisoformat(latest_event["eventTime"].replace("Z", "+00:00"))
        return None
    except Exception as e:
        print(f"Error getting latest event time: {str(e)}")
        return None


def main():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["JewWatch"]

    # Load URL to country mapping
    url_to_country, country_code_to_name = load_url_to_country_mapping("url-to-country-mapping.txt")
    print(f"Loaded {len(url_to_country)} URL to country mappings")

    gd = gdelt.gdelt(version=2)

    # Get dates for the past year or from last extraction
    end = datetime.now()
    latest_event_time = get_latest_event_time(db)
    start = latest_event_time if latest_event_time else (end - timedelta(days=365))

    print(f"Starting extraction from {start} to {end}")

    # Loop through each day
    current_date = start
    while current_date <= end:
        # Format dates for 1 day intervals
        start_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
        end_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        print(f"Extracting data from {start_date} to {end_date}")

        try:
            results = extract_gdelt_data(gd, start_date, end_date)
            result_df = refactor_data_df(results, url_to_country)
            print(f"Found {len(result_df)} matching articles")

            if len(result_df) > 0:
                mongo_docs = create_mongo_docs(result_df)
                is_inserted = insert_to_mongo(mongo_docs, db, "articles")
                save_docs_event = create_save_docs_event(len(mongo_docs), end_date, is_inserted)
                insert_to_mongo(save_docs_event, db, "events")
                if is_inserted:
                    print(f"Inserted {len(mongo_docs)} documents into MongoDB")
                else:
                    print("Failed to insert documents into MongoDB")

                print(f"Saved data to mongodb")

        except Exception as e:
            print(f"Error processing data for {start_date}: {str(e)}")

        # Increment by 30 minutes
        current_date += timedelta(days=1)


if __name__ == "__main__":
    main()


# Overall Tone (first number): 2.25890529973936
# This is the main sentiment score
# Positive values indicate positive sentiment
# Negative values indicate negative sentiment
# The magnitude indicates the strength of the sentiment
# Positive Tone (second number): 4.77845351867941
# Measures the positive aspects of the text
# Higher values indicate more positive language
# Negative Tone (third number): 2.51954821894005
# Measures the negative aspects of the text
# Higher values indicate more negative language
# Polarity (fourth number): 7.29800173761946
# The difference between positive and negative tone
# Indicates how polarized the text is
# Activity (fifth number): 20.9383145091225
# Measures the level of activity or action in the text
# Higher values indicate more active/energetic language
# Emotionality (sixth number): 1.30321459600348
# Measures the emotional intensity of the text
# Higher values indicate more emotional language
# Word Count (seventh number): 1026
# The number of words analyzed in the text
