from pymongo import MongoClient, UpdateOne
from typing import List, Dict
import re
from data.mapping_data.classification_data import against_israel_themes, against_israel_keywords

# ---------------------------
# MongoDB Configuration
# ---------------------------
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "JewWatch"
COLLECTION_NAME = "articles"

# ---------------------------
# Classification Configuration
# ---------------------------
TONE_WEIGHTS = {
    "overall": 2.0,  # Overall tone — neutral/mixed vs clear sentiment
    "positive": -1.0,  # Positive tones reduce suspicion of anti-Israel bias
    "negative": 2.0,  # Negative tones increase suspicion
    "polarity": 1.0,  # Polarity only strongly indicates bias when combined with negative tone
    "emotionality": 0.5,  # Emotional language may indicate bias
    "activity": 0.2,  # Less important, but included to reflect energy in the language
}

THEME_WEIGHT = 1.0  # Weight per matching theme
KEYWORD_WEIGHT = 2.0  # Weight per matching keyword
CLASSIFICATION_THRESHOLD = 7.0  # Final score threshold for classifying as 'against Israel'

# ---------------------------
# Classification Functions
# ---------------------------


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


# ---------------------------
# MongoDB Batch Classification
# ---------------------------


def run_classification():
    """
    Connects to MongoDB, retrieves all articles, classifies each one as
    'isAgainstIsrael' based on tone/theme/keyword analysis, and upserts
    the result into the same document.
    """
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    print("[INFO] Fetching all articles from MongoDB...")
    articles = list(collection.find({}))
    print(f"[INFO] Fetched {len(articles)} articles.")
    
    articles_not_against_israel = [article for article in articles if article['isAgainstIsrael'] == False]

    updates = []
    for article in articles:
        text = article.get("pageTitle", "")
        tones = article.get("tones", {})
        themes = article.get("themes", "")
        suspected = classify_article(text, tones, themes)
        updates.append(UpdateOne({"_id": article["_id"]}, {"$set": {"isAgainstIsrael": suspected}}))

    if updates:
        result = collection.bulk_write(updates)
        print(f"[INFO] Updated {result.modified_count} articles with 'isAgainstIsrael'.")
    else:
        print("[INFO] No articles found for classification.")


# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    run_classification()
