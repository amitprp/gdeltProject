from pymongo import MongoClient
from .config import settings
import logging
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
client = MongoClient(settings.MONGODB_URI)
db = client["JewWatch"]
articles_collection = db["against_israel"]