from pymongo import MongoClient, UpdateOne
from typing import List, Dict
import re
from data.mapping_data.classification_data import against_israel_themes, against_israel_keywords
from data_extraction.utlis import classify_article

# ---------------------------
# MongoDB Configuration
# ---------------------------
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "JewWatch"
COLLECTION_NAME = "articles"

# ---------------------------
# Classification Configuration
# ---------------------------


# ---------------------------
# Classification Functions
# ---------------------------

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
