from pymongo import MongoClient, UpdateOne
from typing import List, Dict
import re

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
    "overall": 2.0,         # Overall tone — neutral/mixed vs clear sentiment
    "positive": -1.0,       # Positive tones reduce suspicion of anti-Israel bias
    "negative": 2.0,        # Negative tones increase suspicion
    "polarity": 2.5,        # High polarity suggests biased/strong sentiment
    "emotionality": 0.5,    # Emotional language may indicate bias
    "activity": 0.2,        # Less important, but included to reflect energy in the language
}

THEME_WEIGHT = 1.0         # Weight per matching theme
KEYWORD_WEIGHT = 2.0       # Weight per matching keyword
CLASSIFICATION_THRESHOLD = 5.0  # Final score threshold for classifying as 'against Israel'

# ---------------------------
# Against-Israel Tags
# ---------------------------
AGAINST_ISRAEL_KEYWORDS = [
    "genocide", "occupation", "apartheid", "ethnic cleansing",
    "zionist aggression", "war crimes", "massacre",
    "israeli brutality", "settler violence", "child casualties",
    "killed by israeli", "displaced by israel", "gaza siege",
    "anti-israel", "pro-palestine protest", "student protest israel"
]

AGAINST_ISRAEL_THEMES = [
    "CRISISLEX_T11_UPDATESSYMPATHY", "CRISISLEX_CRISISLEXREC", "ACT_FORCEPOSTURE",
    "ARREST", "WB_1014_CRIMINAL_JUSTICE", "SECURITY_SERVICES", "TAX_FNCACT_POLICE",
    "CRISISLEX_C07_SAFETY", "EPU_CATS_MIGRATION_FEAR_FEAR", "PROTEST", "VIOLENCE"
]

# ---------------------------
# Classification Functions
# ---------------------------

def compute_sentiment_score(tones: Dict[str, float]) -> float:
    """
    Computes a weighted score based on tone values.
    Higher score = higher likelihood of negative bias toward Israel.
    
    Parameters:
        tones (dict): Dictionary containing tone metrics like 'overall', 'positive', 'negative', etc.
    
    Returns:
        float: Weighted sentiment score
    """
    score = 0.0
    for key, weight in TONE_WEIGHTS.items():
        value = tones.get(key, 0.0)
        score += value * weight
    return score

def extract_theme_ids(theme_str: str) -> List[str]:
    """
    Extracts theme tags (like CRISISLEX_xxx, WB_yyy) from a long theme string.
    
    Parameters:
        theme_str (str): Raw themes string from article
    
    Returns:
        List[str]: List of normalized theme codes
    """
    return re.findall(r'[A-Z_]+', theme_str)

def theme_score(theme_str: str, against_themes: List[str]) -> float:
    """
    Scores the article based on matching themes that are considered anti-Israel.
    
    Parameters:
        theme_str (str): Raw themes string from article
        against_themes (list): List of themes considered 'against Israel'
    
    Returns:
        float: Score based on theme matches
    """
    themes = extract_theme_ids(theme_str)
    hits = sum(1 for theme in themes if theme in against_themes)
    return hits * THEME_WEIGHT

def keyword_score(text: str, keywords: List[str]) -> float:
    """
    Scores the article based on the presence of specific anti-Israel keywords.
    
    Parameters:
        text (str): Combined page title and URL
        keywords (list): List of keywords considered 'against Israel'
    
    Returns:
        float: Score based on keyword matches
    """
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return hits * KEYWORD_WEIGHT

def classify_article(text: str, tones: Dict[str, float], theme_str: str) -> bool:
    """
    Combines tone score, theme score, and keyword score to classify the article.
    
    Parameters:
        text (str): Article's title + URL
        tones (dict): Tone scores
        theme_str (str): Themes string
    
    Returns:
        bool: True if article is suspected to be against Israel (susAgainstIsrael = True)
    """
    score = 0.0
    score += compute_sentiment_score(tones)
    score += theme_score(theme_str, AGAINST_ISRAEL_THEMES)
    score += keyword_score(text, AGAINST_ISRAEL_KEYWORDS)
    return score >= CLASSIFICATION_THRESHOLD

# ---------------------------
# MongoDB Batch Classification
# ---------------------------

def run_classification():
    """
    Connects to MongoDB, retrieves all articles, classifies each one as
    'susAgainstIsrael' based on tone/theme/keyword analysis, and upserts
    the result into the same document.
    """
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    updates = []

    for article in collection.find({}):
        _id = article["_id"]
        text = article.get("pageTitle", "") + " " + article.get("pageUrl", "")
        tones = article.get("tones", {})
        themes = article.get("themes", "")

        suspected = classify_article(text, tones, themes)

        updates.append(UpdateOne(
            {"_id": _id},
            {"$set": {"susAgainstIsrael": suspected}}
        ))

    if updates:
        result = collection.bulk_write(updates)
        print(f"Updated {result.modified_count} articles with 'susAgainstIsrael'.")
    else:
        print("No articles found for classification.")

# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    run_classification()