from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client["JewWatch"]
articles_collection = db["articles"]
