from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
from gdeltdoc import GdeltDoc, Filters
import gdelt
from ..core.database import articles_collection
import logging

# Configure logging
logger = logging.getLogger(__name__)

class GdeltService:
    def __init__(self):
        self.gd = GdeltDoc()
        self.gd2 = gdelt.gdelt(version=2)
        
    async def get_antisemitic_articles(self, days_back: int = 3) -> List[Dict[str, Any]]:
        """Fetch articles related to antisemitism from the last N days."""
        if days_back < 0:
            raise ValueError("days_back must be positive")
            
        try:
            start_date = datetime.now() - timedelta(days=days_back)
            end_date = datetime.now()
            
            # Create GDELT filters
            f = Filters(
                keyword=["Jews", "antisemitism", "Zionism", "Israel hate"],
                start_date=start_date,
                end_date=end_date
            )
            
            # Get articles
            articles = self.gd.article_search(f)
            if articles is None or articles.empty:
                return []
                
            # Transform to list of dictionaries
            articles_list = [{
                "url": row["url"],
                "title": row["title"],
                "seendate": pd.to_datetime(row["seendate"]).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "sourcecountry": row.get("sourcecountry", None),
                "tone": float(row.get("tone", 0)),
                "domain": row.get("domain", None)
            } for _, row in articles.iterrows()]
            
            # Store in MongoDB
            if articles_list:
                try:
                    await articles_collection.insert_many(articles_list)
                except Exception as e:
                    logger.error(f"Error storing articles in MongoDB: {str(e)}")
                    # Continue even if MongoDB storage fails
                    pass
                
            return articles_list
            
        except Exception as e:
            logger.error(f"Error in get_antisemitic_articles: {str(e)}")
            return []
        
    async def get_realtime_mentions(self) -> Dict[str, Any]:
        """Get real-time mentions and sentiment analysis."""
        try:
            # Get the last 15 minutes of news
            now = datetime.now()
            start_time = now - timedelta(minutes=15)
            
            f = Filters(
                keyword=["Jews", "antisemitism", "Zionism", "Israel"],
                start_date=start_time
            )
            
            articles = self.gd.article_search(f)
            if articles is None:
                return {"articles": [], "sentiment": 0.0, "total_mentions": 0}
                
            # Process articles
            articles_list = [{
                "url": row["url"],
                "title": row["title"],
                "seendate": row["seendate"],
                "sourcecountry": row.get("sourcecountry"),
                "tone": row.get("tone"),
                "domain": row.get("domain")
            } for _, row in articles.iterrows()]
            
            # Calculate sentiment
            sentiment = articles["tone"].mean() if not articles.empty else 0.0
            
            return {
                "articles": articles_list,
                "sentiment": sentiment,
                "total_mentions": len(articles_list)
            }
                
            
        except Exception as e:
            logger.error(f"Error in get_realtime_mentions: {str(e)}")
            return {"articles": [], "sentiment": 0, "total_mentions": 0}
            
    async def get_historical_data(self, days: int = 90) -> Dict[str, Any]:
        """Get historical data for trend analysis."""
        if days < 0:
            raise ValueError("days must be positive")
            
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get articles for the period
            f = Filters(
                keyword=["Jews", "antisemitism", "Zionism", "Israel hate"],
                start_date=start_date,
                end_date=end_date
            )
            
            articles = self.gd.article_search(f)
            if articles is None:
                return {
                    "timeline": [],
                    "top_countries": [],
                    "top_sources": []
                }
            
            # Process timeline data
            articles["date"] = pd.to_datetime(articles["seendate"]).dt.date
            timeline = articles.groupby("date").agg({
                "url": "count"
            }).reset_index()
            timeline_data = [{
                "date": str(row["date"]),
                "count": int(row["url"])
            } for _, row in timeline.iterrows()]
            
            # Process country data
            country_counts = articles["sourcecountry"].value_counts()
            country_data = [{
                "country": country,
                "count": int(count)
            } for country, count in country_counts.items() if pd.notna(country)][:10]
            
            # Process source data
            source_counts = articles["domain"].value_counts()
            source_data = [{
                "source": source,
                "count": int(count)
            } for source, count in source_counts.items() if pd.notna(source)][:10]
            
            return {
                "timeline": timeline_data,
                "top_countries": country_data,
                "top_sources": source_data
            }
            
        except Exception as e:
            logger.error(f"Error in get_historical_data: {str(e)}")
            return {
                "timeline": [],
                "top_countries": [],
                "top_sources": []
            }

