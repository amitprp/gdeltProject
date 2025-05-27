from pymongo import MongoClient
from .config import settings

client = MongoClient(settings.MONGO_URI)
db = client["JewWatch"]
articles_collection = db["articles"]
# subset = articles_collection.find().limit(10000)
# db["articles_subset"].insert_many(subset)
# subset_collection = db["articles_subset"]
