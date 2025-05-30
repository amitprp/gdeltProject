from pymongo import MongoClient
import logging
from datetime import datetime
import sys
import os

# Add the parent directory to sys.path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def filter_and_create_collection():
    try:
        # Connect to MongoDB
        client = MongoClient(settings.MONGO_URI)
        db = client["JewWatch"]
        
        # Source and target collections
        source_collection = db['articles']
        target_collection = db['filtered_articles']
        
        # Log total number of documents
        total_docs = source_collection.count_documents({})
        logger.info(f"Total documents in source collection: {total_docs}")
        
        # First stage filter
        pipeline = [
            {
                "$match": {
                    "isAgainstIsrael": True,
                    "sourceCountry": {"$ne": None},
                    "pageAuthors": {"$ne": None}
                }
            }
        ]
        
        # Execute the aggregation pipeline
        filtered_articles = list(source_collection.aggregate(pipeline))
        logger.info(f"Articles matching basic criteria: {len(filtered_articles)}")
        
        # Additional filtering in Python for string length
        filtered_articles = [
            article for article in filtered_articles 
            if isinstance(article.get('pageAuthors'), str) and 
            6 <= len(article['pageAuthors']) < 20
        ]
        
        logger.info(f"Articles after length filter: {len(filtered_articles)}")
        
        if not filtered_articles:
            logger.warning("No articles found matching all criteria")
            return
        
        # Drop the target collection if it exists
        if "filtered_articles" in db.list_collection_names():
            target_collection.drop()
        
        # Insert the filtered articles into the new collection
        result = target_collection.insert_many(filtered_articles)
        
        # Log the results
        logger.info(f"Successfully created new collection 'filtered_articles'")
        logger.info(f"Inserted {len(result.inserted_ids)} documents into the new collection")
        
        # Show a sample article
        if filtered_articles:
            sample = filtered_articles[0]
            logger.info("\nSample article:")
            logger.info(f"Title: {sample.get('pageTitle', 'No Title')}")
            logger.info(f"Authors: {sample.get('pageAuthors', 'No Authors')}")
            logger.info(f"Country: {sample.get('sourceCountry', 'No Country')}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    filter_and_create_collection() 