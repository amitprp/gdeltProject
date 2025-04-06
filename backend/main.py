import subprocess
import os
import logging
from fastapi import FastAPI, Query
from datetime import datetime, timedelta
import pandas as pd
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from gdeltdoc import GdeltDoc, Filters
import gdelt

from typing import List

# Set up logging to output to the console
logging.basicConfig(level=logging.INFO)

app = FastAPI()
# Version 2 queries
gd2 = gdelt.gdelt(version=2)
gd = GdeltDoc()

MONGO_URI = "mongodb+srv://amitprp:KynQcr9eZnR298iw@jewwatch.2pzabjy.mongodb.net/JewWatch"

client = AsyncIOMotorClient(MONGO_URI)
db = client["JewWatch"]
articles_collection = db["articles"]


def transform_data(articles: pd.DataFrame):
    articles_list = articles.to_dict(orient="records")

    # Transform the response into the desired format
    result = {}
    for article in articles_list:
        country = article.get("sourcecountry", "Unknown")  # Default to "Unknown" if missing
        entry = (article["url"], article["title"], article["seendate"])

        if country in result:
            result[country].append(entry)
        else:
            result[country] = [entry]
    return result

@app.get("/articles")
async def get_articles():
    articles = []
    async for article in articles_collection.find({}):
        articles.append({
            "url": article.get("url"),
            "title": article.get("title"),
            "seendate": article.get("seen_date"),
            "country": article.get("article_origin_country")
        })
    return {"articles": articles}


@app.get("/antisemitic-articles")
def get_antisemitic_articles():
    """
    Fetches news articles mentioning "Jews", "antisemitism", "Zionism", "Israel hate", etc.
    Returns URLs and themes.
    """
    query = (
        "antisemitism OR 'Jew hate' OR Zionism OR 'anti-Jewish' OR 'Israel apartheid'"
    )
    gkg_results = gd2.Search(query, table="gkg")

    df = gkg_results[["DocumentIdentifier", "V2Themes", "V2Persons", "V2Organizations"]]
    return df.to_dict(orient="records")

@app.get("/")
def read_root():
    # Log when the server starts
    logging.info(f"Starting the FastAPI server on http://127.0.0.1:8000")
    return {"message": "Hello, FastAPI!"}


@app.get("/gdelt-doc")
async def get_gdelt_doc():

    gd = GdeltDoc()

    filters = Filters(
        keyword="antisemitism", start_date="2025-03-01", end_date="2025-03-30"
    )

    articles = gd.article_search(filters)
    return articles


@app.get("/real_time_articles")
async def real_time_antisemitism():
    f = Filters(
        keyword=["hate Jews", "kill Jews", "Jews are evil", "Jewish problem", "Zionists control", "antisemitic"],
        timespan="1d",  # Get the last 24 hours
        tone="<-5",  # Only very negative articles
        theme="HATE_SPEECH",  # Capture hate speech content
        language="eng"  # English articles (change if needed)
    )

    try:
        articles = gd.article_search(f)
        result = transform_data(articles)

        return result
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Get the current working directory (the root of the project)
    project_root = os.path.dirname(os.path.abspath(__file__))

    # Calculate the path to the virtual environment's Python executable and Uvicorn
    venv_python = os.path.join(project_root, "venv", "bin", "python")
    uvicorn_path = os.path.join(project_root, "venv", "bin", "uvicorn")

    # Ensure the subprocess runs with the correct Python and Uvicorn from the virtual environment
    subprocess.run(
        [
            venv_python,
            uvicorn_path,
            "main:app",
            "--reload",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ]
    )
