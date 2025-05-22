from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, cast
from ..core.database import articles_collection
from ..utils.country_utils import get_country_name
import logging
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseService:
    @staticmethod
    def _ensure_timezone_aware(dt: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is timezone-aware by converting naive datetimes to UTC."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    async def get_articles_with_filters(
        match_pipeline: Dict[str, Any]
    ) -> List[dict]:
        """Base method to get articles with filters."""
        try:
            cursor = articles_collection.find(match_pipeline)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error fetching articles: {str(e)}")
            return []

    @staticmethod
    async def aggregate_articles(pipeline: List[Dict[str, Any]]) -> List[dict]:
        """Base method to perform aggregation on articles."""
        try:
            cursor = articles_collection.aggregate(pipeline)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error in aggregation: {str(e)}")
            return []

    @staticmethod
    async def get_articles_by_date_range(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get articles within a date range."""
        match_pipeline: Dict[str, Any] = {}
        if start_date or end_date:
            date_filter: Dict[str, datetime] = {}
            start = DatabaseService._ensure_timezone_aware(start_date)
            end = DatabaseService._ensure_timezone_aware(end_date)
            if start:
                date_filter["$gte"] = start
            if end:
                date_filter["$lte"] = end
            if date_filter:
                match_pipeline["date.isoDate"] = date_filter
        
        return await DatabaseService.get_articles_with_filters(match_pipeline)

    @staticmethod
    async def get_articles_by_source(
        country: Optional[str] = None,
        author: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get articles filtered by source attributes."""
        match_pipeline = {}
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            match_pipeline["date.isoDate"] = date_filter
            
        if country:
            match_pipeline["sourceCountry"] = country
            
        if author:
            match_pipeline["pageAuthors"] = author
            
        return await DatabaseService.get_articles_with_filters(match_pipeline)

    @staticmethod
    async def get_grouped_articles(
        group_field: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get articles grouped by a specific field with statistics."""
        try:
            match_stage = {}
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                match_stage["date.isoDate"] = date_filter

            pipeline = [
                {"$match": match_stage} if match_stage else {},
                {
                    "$match": {
                        group_field: {"$exists": True, "$ne": None, "$ne": ""}
                    }
                },
                {
                    "$group": {
                        "_id": f"${group_field}",
                        "articleCount": {"$sum": 1},
                        "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                        "lastArticleDate": {"$max": "$date.isoDate"},
                        "articles": {
                            "$push": {
                                "title": {"$ifNull": ["$pageTitle", "No Title"]},
                                "url": {"$ifNull": ["$pageUrl", "#"]},
                                "date": "$date.isoDate",
                                "tone": {"$ifNull": ["$tones.overall", 0]}
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "name": "$_id",
                        "articleCount": 1,
                        "averageTone": {"$divide": ["$totalTone", "$articleCount"]},
                        "lastArticleDate": 1,
                        "recentArticles": {"$slice": ["$articles", 5]}
                    }
                },
                {"$sort": {"articleCount": -1}}
            ]

            results = await DatabaseService.aggregate_articles(pipeline)
            
            # Convert country codes to names if needed
            if group_field == "sourceCountry":
                for result in results:
                    if result["name"]:
                        result["name"] = get_country_name(result["name"])
            
            return results
        except Exception as e:
            logger.error(f"Error in get_grouped_articles: {str(e)}")
            return []

    @staticmethod
    async def get_top_countries_by_articles(
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get top countries by article count with their average tone."""
        try:
            match_stage = {}
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                match_stage["date.isoDate"] = date_filter

            pipeline = [
                {"$match": match_stage} if match_stage else {},
                {
                    "$match": {
                        "sourceCountry": {"$exists": True, "$ne": None, "$ne": ""}
                    }
                },
                {
                    "$group": {
                        "_id": "$sourceCountry",
                        "value": {"$sum": 1},
                        "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "code": "$_id",
                        "value": 1,
                        "averageTone": {"$divide": ["$totalTone", "$value"]}
                    }
                },
                {"$sort": {"value": -1}},
                {"$limit": limit}
            ]

            results = await DatabaseService.aggregate_articles(pipeline)
            
            # Convert country codes to names
            for result in results:
                result["name"] = get_country_name(result["code"])
            
            return results
        except Exception as e:
            logger.error(f"Error in get_top_countries_by_articles: {str(e)}")
            return []

    @staticmethod
    async def get_global_statistics() -> dict:
        """Get global statistics about articles."""
        try:
            pipeline = [
                {
                    "$match": {
                        "sourceCountry": {"$exists": True, "$ne": None, "$ne": ""}
                    }
                },
                {
                    "$group": {
                        "_id": "$sourceCountry",
                        "value": {"$sum": 1},
                        "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "code": "$_id",
                        "value": 1,
                        "averageTone": {"$divide": ["$totalTone", "$value"]}
                    }
                },
                {"$sort": {"value": -1}}
            ]

            countries = await DatabaseService.aggregate_articles(pipeline)
            
            # Convert country codes to names and calculate totals
            total_articles = 0
            for country in countries:
                country["name"] = get_country_name(country["code"])
                total_articles += country["value"]

            return {
                "totalArticles": total_articles,
                "countries": countries,
                "averagePerCountry": total_articles / len(countries) if countries else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting global statistics: {str(e)}")
            return {
                "totalArticles": 0,
                "countries": [],
                "averagePerCountry": 0
            }

    @staticmethod
    async def get_country_details(country_code: str) -> Optional[dict]:
        """Get detailed information about a specific country."""
        try:
            pipeline = [
                {
                    "$match": {
                        "sourceCountry": country_code
                    }
                },
                {
                    "$group": {
                        "_id": "$sourceCountry",
                        "value": {"$sum": 1},
                        "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "code": "$_id",
                        "value": 1,
                        "averageTone": {"$divide": ["$totalTone", "$value"]}
                    }
                }
            ]

            results = await DatabaseService.aggregate_articles(pipeline)
            
            # Get country name first to validate country code
            country_name = get_country_name(country_code)
            if not country_name:
                return None  # Invalid country code
            
            # If no articles found, return empty stats with country info
            if not results:
                return {
                    "code": country_code,
                    "name": country_name,
                    "value": 0,
                    "averageTone": 0,
                    "iso2": country_code
                }

            country_data = results[0]
            country_data["name"] = country_name
            country_data["iso2"] = country_code
            
            return country_data
            
        except Exception as e:
            logger.error(f"Error getting country details: {str(e)}")
            return None

    @staticmethod
    async def get_country_time_stats(
        country_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get time-based statistics for a specific country."""
        try:
            # Build match stage with timezone-aware dates
            match_stage: Dict[str, Any] = {"sourceCountry": country_code}
            if start_date or end_date:
                date_filter: Dict[str, datetime] = {}
                start = DatabaseService._ensure_timezone_aware(start_date)
                end = DatabaseService._ensure_timezone_aware(end_date)
                if start:
                    date_filter["$gte"] = start
                if end:
                    date_filter["$lte"] = end
                if date_filter:
                    match_stage["date.isoDate"] = date_filter

            # Get timeline data
            timeline_pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date.isoDate", "timezone": "UTC"}},
                        "count": {"$sum": 1},
                        "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "date": "$_id",
                        "count": 1,
                        "tone": {"$divide": ["$totalTone", "$count"]}
                    }
                },
                {"$sort": {"date": 1}}
            ]

            # Get overall stats and recent articles
            stats_pipeline = [
                {"$match": match_stage},
                {
                    "$facet": {
                        "stats": [
                            {
                                "$group": {
                                    "_id": None,
                                    "articleCount": {"$sum": 1},
                                    "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}}
                                }
                            },
                            {
                                "$project": {
                                    "_id": 0,
                                    "articleCount": 1,
                                    "averageTone": {"$divide": ["$totalTone", "$articleCount"]}
                                }
                            }
                        ],
                        "articles": [
                            {"$sort": {"date.isoDate": -1}},
                            {"$limit": 10},
                            {
                                "$project": {
                                    "_id": 0,
                                    "title": {"$ifNull": ["$pageTitle", "No Title"]},
                                    "url": {"$ifNull": ["$pageUrl", "#"]},
                                    "date": "$date.isoDate",
                                    "source": {"$ifNull": ["$pageAuthors", "Unknown Source"]}
                                }
                            }
                        ]
                    }
                }
            ]

            timeline_data = await DatabaseService.aggregate_articles(timeline_pipeline)
            stats_results = await DatabaseService.aggregate_articles(stats_pipeline)

            # Always return a valid response, even if no articles found
            return {
                "articleCount": stats_results[0]["stats"][0]["articleCount"] if stats_results and stats_results[0]["stats"] else 0,
                "averageTone": stats_results[0]["stats"][0]["averageTone"] if stats_results and stats_results[0]["stats"] else 0,
                "timelineData": timeline_data or [],
                "articles": stats_results[0]["articles"] if stats_results else []
            }
            
        except Exception as e:
            logger.error(f"Error getting country time stats: {str(e)}")
            return {
                "articleCount": 0,
                "averageTone": 0,
                "timelineData": [],
                "articles": []
            }

    @staticmethod
    async def compare_time_periods(
        timeframe1_start: datetime,
        timeframe1_end: datetime,
        timeframe2_start: datetime,
        timeframe2_end: datetime
    ) -> List[dict]:
        """Compare article trends between two time periods."""
        try:
            # Ensure all dates are timezone-aware
            tf1_start = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe1_start))
            tf1_end = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe1_end))
            tf2_start = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe2_start))
            tf2_end = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe2_end))

            # Create pipelines for both timeframes
            async def get_timeframe_data(start_date: datetime, end_date: datetime) -> dict:
                pipeline = [
                    {
                        "$match": {
                            "date.isoDate": {
                                "$gte": start_date,
                                "$lte": end_date
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date.isoDate", "timezone": "UTC"}},
                            "articleCount": {"$sum": 1},
                            "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}}
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "date": "$_id",
                            "articleCount": 1,
                            "averageTone": {"$divide": ["$totalTone", "$articleCount"]}
                        }
                    },
                    {"$sort": {"date": 1}}
                ]
                
                results = await DatabaseService.aggregate_articles(pipeline)
                total_articles = sum(day["articleCount"] for day in results)
                
                return {
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "articleCount": total_articles,
                    "dailyData": results
                }

            # Get data for both timeframes
            [timeframe1_data, timeframe2_data] = await asyncio.gather(
                get_timeframe_data(tf1_start, tf1_end),
                get_timeframe_data(tf2_start, tf2_end)
            )

            return [timeframe1_data, timeframe2_data]
            
        except Exception as e:
            logger.error(f"Error comparing time periods: {str(e)}")
            return [
                {
                    "startDate": timeframe1_start.isoformat(),
                    "endDate": timeframe1_end.isoformat(),
                    "articleCount": 0,
                    "dailyData": []
                },
                {
                    "startDate": timeframe2_start.isoformat(),
                    "endDate": timeframe2_end.isoformat(),
                    "articleCount": 0,
                    "dailyData": []
                }
            ] 