from pymongo import MongoClient
from .config import settings

client = MongoClient(settings.MONGO_URI)
db = client["JewWatch"]
# articles_collection = db["articles"]
articles_collection = db["new_articles"]
