from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, cast, Union
from ..core.database import articles_collection
from ..utils.country_utils import get_country_name, get_country_code
import logging
import traceback

# Configure logging
logger = logging.getLogger(__name__)

# Define MongoDB pipeline stage types
PipelineStage = Dict[str, Any]
Pipeline = List[PipelineStage]

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
    def get_articles_with_filters(match_pipeline: Dict[str, Any]) -> List[dict]:
        """Base method to get articles with filters."""
        try:
            cursor = articles_collection.find(match_pipeline)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error fetching articles: {str(e)}")
            return []

    @staticmethod
    def aggregate_articles(pipeline: List[Dict[str, Any]]) -> List[dict]:
        """Base method to perform aggregation on articles."""
        try:
            cursor = articles_collection.aggregate(pipeline)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error in aggregation: {str(e)}")
            return []

    @staticmethod
    def get_articles_by_date_range(
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
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

        return DatabaseService.get_articles_with_filters(match_pipeline)

    @staticmethod
    def get_articles_by_source(
        country: Optional[str] = None,
        author: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[dict]:
        """Get articles filtered by source attributes."""
        try:
            # Build match stage
            match_stage: Dict[str, Any] = {}
                        # Ensure dates are timezone-aware
            start = DatabaseService._ensure_timezone_aware(start_date)
            end = DatabaseService._ensure_timezone_aware(end_date)
            
            logger.info(f"Getting grouped articles for field: {'country: ' + country if country else 'author: ' + (author or '')}, start_date: {start}, end_date: {end}")
            
            
            pipeline: Pipeline = []
            
            # Only add match stage if we have date filters
            if start or end:
                date_filter: Dict[str, Any] = {}
                if start:
                    date_filter["$gte"] = start.isoformat()
                if end:
                    date_filter["$lte"] = end.isoformat()
                
                match_stage["date.isoDate"] = date_filter
                logger.info(f"Added date filter to pipeline: {date_filter}")

            if country:
                # Convert country name to code if it's a full name
                country_code = get_country_code(country)
                logger.info(f"Input country: {country}")
                logger.info(f"Converted country code: {country_code}")
                
                # Check if we got a valid country code
                if country_code:
                    match_stage["sourceCountry"] = country_code
                else:
                    # If no valid code found, try the original input
                    match_stage["sourceCountry"] = country
                
                logger.info(f"Final country search value: {match_stage.get('sourceCountry')}")

            if author:
                author_lower = author.lower()
                match_stage["$expr"] = {
                    "$cond": {
                        "if": {
                            "$or": [
                                {"$eq": ["$pageAuthors", None]},
                                {"$eq": ["$pageAuthors", ""]},
                                {"$eq": ["$pageAuthors", []]}
                            ]
                        },
                        "then": {"$eq": [author_lower, "unknown"]},
                        "else": {
                            "$cond": {
                                "if": {"$isArray": "$pageAuthors"},
                                "then": {
                                    "$in": [
                                        author_lower,
                                        {
                                            "$map": {
                                                "input": "$pageAuthors",
                                                "as": "author",
                                                "in": {"$toLower": "$$author"}
                                            }
                                        }
                                    ]
                                },
                                "else": {"$eq": [{"$toLower": "$pageAuthors"}, author_lower]}
                            }
                        }
                    }
                }
                logger.info(f"Author search expression: {match_stage['$expr']}")

            # Log the match stage for debugging
            logger.info(f"Final match stage: {match_stage}")

            # Create aggregation pipeline
            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": {
                            "country": "$sourceCountry",
                            "author": {
                                "$cond": {
                                    "if": {
                                        "$or": [
                                            {"$eq": ["$pageAuthors", None]},
                                            {"$eq": ["$pageAuthors", ""]},
                                            {"$eq": ["$pageAuthors", []]},
                                            {"$eq": [{"$type": "$pageAuthors"}, "missing"]}
                                        ]
                                    },
                                    "then": "Unknown",
                                    "else": "$pageAuthors"
                                }
                            }
                        },
                        "articleCount": {"$sum": 1},
                        "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                        "lastArticleDate": {"$max": "$date.isoDate"},
                        "articles": {
                            "$push": {
                                "title": {"$ifNull": ["$pageTitle", "No Title"]},
                                "url": {"$ifNull": ["$pageUrl", "#"]},
                                "date": "$date.isoDate",
                                "tone": {"$ifNull": ["$tones.overall", 0]},
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "source": {
                            "$cond": {
                                "if": {
                                    "$or": [
                                        {"$eq": ["$_id.author", None]},
                                        {"$eq": ["$_id.author", ""]},
                                        {"$eq": ["$_id.author", []]},
                                        {"$eq": ["$_id.author", "Unknown"]}
                                    ]
                                },
                                "then": "Unknown",
                                "else": "$_id.author"
                            }
                        },
                        "country": {
                            "$cond": {
                                "if": {"$or": [
                                    {"$eq": ["$_id.country", None]},
                                    {"$eq": ["$_id.country", ""]},
                                ]},
                                "then": "Unknown",
                                "else": "$_id.country"
                            }
                        },
                        "articleCount": 1,
                        "averageTone": {"$divide": ["$totalTone", "$articleCount"]},
                        "lastArticleDate": 1,
                        "recentArticles": {"$slice": ["$articles", 5]}
                    }
                },
                {"$sort": {"articleCount": -1}}
            ]

            # Execute the pipeline and get results
            results = DatabaseService.aggregate_articles(pipeline)
            logger.info(f"Found {len(results)} results before processing")
            
            # Post-process results to convert country codes to names
            processed_results = []
            for result in results:
                # Convert country code to name
                if result["country"] != "Unknown":
                    country_name = get_country_name(result["country"])
                    result["country"] = country_name if country_name else result["country"]
                
                # Handle source field
                if isinstance(result["source"], list):
                    # If source is a list, join with commas
                    result["source"] = ", ".join(filter(None, result["source"]))
                elif result["source"] is None or result["source"] == "":
                    result["source"] = "Unknown"
                
                processed_results.append(result)
            
            logger.info(f"Final processed results: {processed_results}")
            return processed_results

        except Exception as e:
            logger.error(f"Error fetching articles: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    @staticmethod
    def get_grouped_articles(
        group_field: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get articles grouped by a specific field with statistics."""
        try:
            # First, let's verify we have data in the collection
            sample_doc = articles_collection.find_one()
            logger.info(f"Sample document date format: {sample_doc.get('date') if sample_doc else 'No documents found'}")
            
            # Ensure dates are timezone-aware
            start = DatabaseService._ensure_timezone_aware(start_date)
            end = DatabaseService._ensure_timezone_aware(end_date)
            
            logger.info(f"Getting grouped articles for field: {group_field}, start_date: {start}, end_date: {end}")
            
            pipeline: Pipeline = []
            
            # Only add match stage if we have date filters
            if start or end:
                date_match: Dict[str, Any] = {}
                if start:
                    date_match["$gte"] = start.isoformat()
                if end:
                    date_match["$lte"] = end.isoformat()
                
                pipeline.append({
                    "$match": {"date.isoDate": date_match}
                })
                logger.info(f"Added date filter to pipeline: {date_match}")

            # Add document limit after date filter for better performance
            pipeline.append({"$limit": 10000})

            # Handle null/empty values before grouping
            pipeline.append({
                "$set": {
                    group_field: {
                        "$cond": {
                            "if": {"$or": [
                                {"$eq": [f"${group_field}", None]},
                                {"$eq": [f"${group_field}", ""]},
                                {"$eq": [f"${group_field}", []]},
                            ]},
                            "then": "Unknown",
                            "else": f"${group_field}"
                        }
                    }
                }
            })

            # For author grouping, we need to handle arrays
            if group_field == "pageAuthors":
                pipeline.extend([
                    # Unwind arrays of authors
                    {"$unwind": {"path": f"${group_field}", "preserveNullAndEmptyArrays": True}},
                    # Handle any null values that might appear after unwinding
                    {
                        "$set": {
                            group_field: {
                                "$cond": {
                                    "if": {"$or": [
                                        {"$eq": [f"${group_field}", None]},
                                        {"$eq": [f"${group_field}", ""]},
                                    ]},
                                    "then": "Unknown",
                                    "else": f"${group_field}"
                                }
                            }
                        }
                    }
                ])

            # Add field existence check and other stages
            pipeline.extend([
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
                                "tone": {"$ifNull": ["$tones.overall", 0]},
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "name": {
                            "$cond": {
                                "if": {"$eq": ["$_id", None]},
                                "then": "Unknown",
                                "else": {"$toString": "$_id"}
                            }
                        },
                        "articleCount": 1,
                        "averageTone": {"$divide": ["$totalTone", "$articleCount"]},
                        "lastArticleDate": 1,
                        "recentArticles": {"$slice": ["$articles", 5]}
                    }
                },
                {
                    "$sort": {"articleCount": -1}
                }
            ])

            logger.info(f"Executing pipeline: {pipeline}")
            results = DatabaseService.aggregate_articles(pipeline)
            logger.info(f"Found {len(results)} results")

            # Let's also log a sample of matching documents for debugging
            if len(results) == 0 and (start or end):
                sample_matches = list(articles_collection.find(
                    {"date.isoDate": date_match} if start or end else {}
                ).limit(1))
                logger.info(f"Sample documents in date range: {sample_matches}")

            # Convert country codes to names if needed
            if group_field == "sourceCountry":
                for result in results:
                    if result["name"] and result["name"] != "Unknown":
                        result["name"] = get_country_name(result["name"])

            return results
        except Exception as e:
            logger.error(f"Error in get_grouped_articles: {str(e)}")
            logger.error(f"Pipeline that caused error: {pipeline}")
            return []

    @staticmethod
    def get_top_countries_by_articles(
        limit: int = 10, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
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
                {"$match": {"sourceCountry": {"$exists": True, "$ne": None, "$ne": ""}}},
                {
                    "$group": {
                        "_id": "$sourceCountry",
                        "value": {"$sum": 1},
                        "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "code": "$_id",
                        "value": 1,
                        "averageTone": {"$divide": ["$totalTone", "$value"]},
                    }
                },
                {"$sort": {"value": -1}},
                {"$limit": limit},
            ]

            results = DatabaseService.aggregate_articles(pipeline)

            # Convert country codes to names and add iso2
            for result in results:
                result["name"] = get_country_name(result["code"])
                result["iso2"] = result["code"]  # Add iso2 field to match FileDBService

            return results
        except Exception as e:
            logger.error(f"Error in get_top_countries_by_articles: {str(e)}")
            return []

    @staticmethod
    def get_global_statistics() -> dict:
        """Get global statistics about articles."""
        try:
            # First get total article count without any filtering
            total_pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": 1}
                    }
                }
            ]
            total_result = DatabaseService.aggregate_articles(total_pipeline)
            total_articles = total_result[0]["total"] if total_result else 0

            # Then get country-specific statistics
            country_pipeline = [
                {"$match": {"sourceCountry": {"$exists": True, "$ne": None, "$ne": ""}}},
                {
                    "$group": {
                        "_id": "$sourceCountry",
                        "value": {"$sum": 1},
                        "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "code": "$_id",
                        "value": 1,
                        "averageTone": {"$divide": ["$totalTone", "$value"]},
                        "iso2": "$_id"  # Add iso2 field directly in the projection
                    }
                },
                {"$sort": {"value": -1}},
            ]

            countries = DatabaseService.aggregate_articles(country_pipeline)

            # Convert country codes to names and ensure all required fields are present
            formatted_countries = []
            for country in countries:
                country_name = get_country_name(country["code"])
                if country_name:  # Only include countries we can identify
                    formatted_country = {
                        "id": country["code"],  # Required for map
                        "code": country["code"],
                        "iso2": country["code"],
                        "name": country_name,
                        "value": country["value"],
                        "averageTone": country["averageTone"]
                    }
                    formatted_countries.append(formatted_country)

            return {
                "totalArticles": total_articles,
                "countries": formatted_countries,
                "averagePerCountry": total_articles / len(formatted_countries) if formatted_countries else 0,
            }

        except Exception as e:
            logger.error(f"Error getting global statistics: {str(e)}")
            return {"totalArticles": 0, "countries": [], "averagePerCountry": 0}

    @staticmethod
    def get_country_details(country_code: str) -> Optional[dict]:
        """Get detailed information about a specific country."""
        try:
            pipeline = [
                {"$match": {"sourceCountry": country_code}},
                {
                    "$group": {
                        "_id": "$sourceCountry",
                        "value": {"$sum": 1},
                        "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "code": "$_id",
                        "value": 1,
                        "averageTone": {"$divide": ["$totalTone", "$value"]},
                    }
                },
            ]

            results = DatabaseService.aggregate_articles(pipeline)

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
                    "iso2": country_code,
                }

            country_data = results[0]
            country_data["name"] = country_name
            country_data["iso2"] = country_code

            return country_data

        except Exception as e:
            logger.error(f"Error getting country details: {str(e)}")
            return None

    @staticmethod
    def get_country_time_stats(
        country_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get time-based statistics for a specific country."""
        try:
            # Build match stage with timezone-aware dates
            match_stage: Dict[str, Any] = {"sourceCountry": country_code}
            
            # Debug: Check if we have any articles for this country before date filtering
            sample_count = articles_collection.count_documents({"sourceCountry": country_code})
            logger.info(f"Total articles found for country {country_code} before date filtering: {sample_count}")
            
            if start_date or end_date:
                date_filter: Dict[str, Any] = {}
                start = DatabaseService._ensure_timezone_aware(start_date)
                end = DatabaseService._ensure_timezone_aware(end_date)
                
                if start:
                    date_filter["$gte"] = start.isoformat()  # Convert to ISO string
                    logger.info(f"Using start date: {start.isoformat()}")
                if end:
                    date_filter["$lte"] = end.isoformat()  # Convert to ISO string
                    logger.info(f"Using end date: {end.isoformat()}")
                if date_filter:
                    match_stage["date.isoDate"] = date_filter
            
            logger.info(f"Match stage: {match_stage}")

            # Get timeline data
            timeline_pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": {
                                    "$dateFromString": {
                                        "dateString": "$date.isoDate",
                                        "timezone": "UTC"
                                    }
                                },
                                "timezone": "UTC"
                            }
                        },
                        "count": {"$sum": 1},
                        "total_tone": {"$sum": {"$ifNull": ["$tones.overall", 0]}}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "date": "$_id",
                        "count": "$count",
                        "tone": {
                            "$cond": [
                                {"$eq": ["$count", 0]},
                                0,
                                {"$divide": ["$total_tone", "$count"]}
                            ]
                        }
                    }
                },
                {"$sort": {"date": 1}}
            ]

            # Debug: Log the pipeline and sample document
            logger.info(f"Timeline pipeline: {timeline_pipeline}")
            sample_doc = articles_collection.find_one(match_stage)
            logger.info(f"Sample document date format: {sample_doc.get('date') if sample_doc else 'No documents found'}")

            # Execute timeline aggregation
            timeline_data = DatabaseService.aggregate_articles(timeline_pipeline)
            logger.info(f"Raw timeline data results: {timeline_data}")

            # Ensure timeline data is properly formatted
            formatted_timeline_data = []
            for item in timeline_data:
                try:
                    formatted_item = {
                        "date": item["date"],
                        "count": int(item["count"]),
                        "tone": float(item.get("tone", 0))
                    }
                    formatted_timeline_data.append(formatted_item)
                except Exception as e:
                    logger.error(f"Error formatting timeline item {item}: {str(e)}")

            logger.info(f"Formatted timeline data: {formatted_timeline_data}")

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
                                    "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                                }
                            },
                            {
                                "$project": {
                                    "_id": 0,
                                    "articleCount": 1,
                                    "averageTone": {
                                        "$cond": [
                                            {"$eq": ["$articleCount", 0]},
                                            0,
                                            {"$divide": ["$totalTone", "$articleCount"]}
                                        ]
                                    }
                                }
                            },
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
                                    "source": {"$ifNull": ["$pageAuthors", "Unknown Source"]},
                                }
                            },
                        ],
                    }
                },
            ]

            stats_results = DatabaseService.aggregate_articles(stats_pipeline)
            logger.info(f"Stats results: {stats_results}")

            # Format the response
            result = {
                "articleCount": (
                    stats_results[0]["stats"][0]["articleCount"]
                    if stats_results and stats_results[0]["stats"]
                    else 0
                ),
                "averageTone": (
                    stats_results[0]["stats"][0]["averageTone"]
                    if stats_results and stats_results[0]["stats"]
                    else 0
                ),
                "timelineData": formatted_timeline_data,
                "articles": stats_results[0]["articles"] if stats_results else [],
            }

            # Log the final result
            logger.info(f"Final result for country {country_code}: {result}")
            
            return result

        except Exception as e:
            logger.error(f"Error getting country time stats: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"articleCount": 0, "averageTone": 0, "timelineData": [], "articles": []}

    @staticmethod
    def compare_time_periods(
        timeframe1_start: datetime,
        timeframe1_end: datetime,
        timeframe2_start: datetime,
        timeframe2_end: datetime,
    ) -> List[dict]:
        """Compare article trends between two time periods."""
        try:
            # Ensure all dates are timezone-aware
            tf1_start = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe1_start))
            tf1_end = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe1_end))
            tf2_start = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe2_start))
            tf2_end = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe2_end))

            # Create pipelines for both timeframes
            def get_timeframe_data(start_date: datetime, end_date: datetime) -> dict:
                # Convert dates to ISO format for MongoDB comparison
                start_iso = start_date.isoformat()
                end_iso = end_date.isoformat()

                pipeline = [
                    {
                        "$match": {
                            "date.isoDate": {
                                "$gte": start_iso,
                                "$lte": end_iso
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": {
                                        "$dateFromString": {
                                            "dateString": "$date.isoDate",
                                            "timezone": "UTC"
                                        }
                                    }
                                }
                            },
                            "articleCount": {"$sum": 1},
                            "totalTone": {"$sum": {"$ifNull": ["$tones.overall", 0]}},
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "date": "$_id",
                            "articleCount": 1,
                            "averageTone": {
                                "$cond": [
                                    {"$eq": ["$articleCount", 0]},
                                    0,
                                    {"$divide": ["$totalTone", "$articleCount"]}
                                ]
                            }
                        }
                    },
                    {"$sort": {"date": 1}},
                ]

                results = DatabaseService.aggregate_articles(pipeline)
                total_articles = sum(day["articleCount"] for day in results)

                return {
                    "startDate": start_iso,
                    "endDate": end_iso,
                    "articleCount": total_articles,
                    "dailyData": results,
                }

            # Get data for both timeframes
            timeframe1_data = get_timeframe_data(tf1_start, tf1_end)
            timeframe2_data = get_timeframe_data(tf2_start, tf2_end)

            return [timeframe1_data, timeframe2_data]

        except Exception as e:
            logger.error(f"Error comparing time periods: {str(e)}")
            return [
                {
                    "startDate": timeframe1_start.isoformat(),
                    "endDate": timeframe1_end.isoformat(),
                    "articleCount": 0,
                    "dailyData": [],
                },
                {
                    "startDate": timeframe2_start.isoformat(),
                    "endDate": timeframe2_end.isoformat(),
                    "articleCount": 0,
                    "dailyData": [],
                },
            ]
