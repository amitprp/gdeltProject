import asyncio
from gdeltdoc import GdeltDoc, Filters
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient

# Connect to MongoDB
# MONGO_URI = "mongodb+srv://<username>:<password>@cluster0.mongodb.net/JewWatch"
# client = AsyncIOMotorClient(MONGO_URI)
# db = client["JewWatch"]
# articles_collection = db["articles"]

# GDELT Client
gd = GdeltDoc()

# Define Keywords
keywords = ["Israel", "Jewish", "Zionist"]


def transform_data(articles: pd.DataFrame):
    articles_list = articles.to_dict(orient="records")

    # Transform the response into the desired format
    result = {}
    for article in articles_list:
        country = article.get(
            "sourcecountry", "Unknown"
        )  # Default to "Unknown" if missing
        entry = (article["url"], article["title"], article["seendate"])

        if country in result:
            result[country].append(entry)
        else:
            result[country] = [entry]
    return result


async def fetch_and_store_articles():
    all_articles = []

    for keyword in keywords:
        print(f"Fetching articles for: {keyword}")

        # Query articles for the last 2 years
        filters = Filters(
            keyword=keyword,
            start_date="2023-01-01",  # Adjust as needed
            end_date="2025-03-30",
        )

        # Fetch articles
        articles = gd.article_search(filters)
        result = transform_data(articles)

        sum_articles = 0

        for country in result:
            sum_articles += len(result[country])

        print(f"Total articles for {keyword}: {sum_articles}")


# Run the script
asyncio.run(fetch_and_store_articles())
