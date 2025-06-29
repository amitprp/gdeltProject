from pymongo import MongoClient
from config import settings
import logging
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
client = MongoClient(settings.MONGO_URI)
db = client["JewWatch"]
articles_collection = db["articles"]
# articles_collection = db["articles_subset"]
# articles_collection = db["new_articles"]
