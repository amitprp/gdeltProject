from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, cast, Union
from ...core.database import articles_collection
from ...utils.country_utils import get_country_name, get_country_code
import logging
import traceback
from .constants import AGGREGATIONS, FILTERS

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
    def _get_aggregation_by_name(name: str) -> Pipeline:
        """Get aggregation pipeline by name from the AGGREGATIONS dictionary."""
        if name not in AGGREGATIONS:
            raise ValueError(f"Aggregation {name} not found")
        return AGGREGATIONS[name]["pipeline"]

    @staticmethod
    def _get_filter_by_name(name: str) -> Dict[str, Any]:
        """Get filter by name from the FILTERS dictionary."""
        if name not in FILTERS:
            raise ValueError(f"Filter {name} not found")
        return FILTERS[name]["filter"]

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
            import copy

            date_filter = copy.deepcopy(DatabaseService._get_filter_by_name("DATE_RANGE_FILTER"))
            if start_date:
                date_filter["date.isoDate"]["$gte"] = start_date
            if end_date:
                date_filter["date.isoDate"]["$lte"] = end_date
            match_pipeline = date_filter
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
            import copy

            match_stage: Dict[str, Any] = {}
            if start_date or end_date:
                date_filter = copy.deepcopy(
                    DatabaseService._get_filter_by_name("DATE_RANGE_FILTER")
                )
                if start_date:
                    date_filter["date.isoDate"]["$gte"] = start_date.isoformat()
                if end_date:
                    date_filter["date.isoDate"]["$lte"] = end_date.isoformat()
                match_stage["date.isoDate"] = date_filter["date.isoDate"]
            if country:
                country_code = get_country_code(country)
                country_filter = copy.deepcopy(
                    DatabaseService._get_filter_by_name("COUNTRY_FILTER")
                )
                country_filter["sourceCountry"] = country_code if country_code else country
                match_stage["sourceCountry"] = country_filter["sourceCountry"]
            if author:
                author_lower = author.lower()
                author_filter = copy.deepcopy(DatabaseService._get_filter_by_name("AUTHOR_FILTER"))

                # Recursively replace <AUTHOR> with author_lower
                def replace_author(obj):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if isinstance(v, str) and v == "<AUTHOR>":
                                obj[k] = author_lower
                            else:
                                replace_author(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            replace_author(item)

                replace_author(author_filter)
                match_stage["$expr"] = author_filter["$expr"]
            pipeline_template = DatabaseService._get_aggregation_by_name("ARTICLES_BY_SOURCE")
            pipeline = copy.deepcopy(pipeline_template)
            pipeline[0]["$match"] = match_stage
            
            # Add a stage to ensure unique articles by title
            pipeline.insert(1, {
                "$group": {
                    "_id": "$pageTitle",
                    "doc": { "$first": "$$ROOT" }
                }
            })
            pipeline.insert(2, {
                "$replaceRoot": { "newRoot": "$doc" }
            })
            
            results = DatabaseService.aggregate_articles(pipeline)
            processed_results = []
            for result in results:
                if result["country"] != "Unknown":
                    country_name = get_country_name(result["country"])
                    result["country"] = country_name if country_name else result["country"]
                if isinstance(result["source"], list):
                    result["source"] = ", ".join(filter(None, result["source"]))
                elif result["source"] is None or result["source"] == "":
                    result["source"] = "Unknown"
                processed_results.append(result)
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
            start = DatabaseService._ensure_timezone_aware(start_date)
            end = DatabaseService._ensure_timezone_aware(end_date)
            date_match = {}
            if start:
                date_match["$gte"] = start.isoformat()
            if end:
                date_match["$lte"] = end.isoformat()
            import copy

            pipeline_template = DatabaseService._get_aggregation_by_name("GROUPED_ARTICLES")
            pipeline = copy.deepcopy(pipeline_template)
            # Inject date match
            pipeline[0]["$match"] = {"date.isoDate": date_match} if date_match else {}

            # Inject group_field in all relevant places
            def replace_group_field(obj):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if isinstance(v, str) and "<GROUP_FIELD>" in v:
                            obj[k] = v.replace("<GROUP_FIELD>", group_field)
                        else:
                            replace_group_field(v)
                elif isinstance(obj, list):
                    for item in obj:
                        replace_group_field(item)

            replace_group_field(pipeline)
            # If group_field == 'pageAuthors', insert unwind and set after the first $set
            if group_field == "pageAuthors":
                pipeline.insert(
                    3, {"$unwind": {"path": f"${group_field}", "preserveNullAndEmptyArrays": True}}
                )
                pipeline.insert(
                    4,
                    {
                        "$set": {
                            group_field: {
                                "$cond": {
                                    "if": {
                                        "$or": [
                                            {"$eq": [f"${group_field}", None]},
                                            {"$eq": [f"${group_field}", ""]},
                                        ]
                                    },
                                    "then": "Unknown",
                                    "else": f"${group_field}",
                                }
                            }
                        }
                    },
                )
            results = DatabaseService.aggregate_articles(pipeline)
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
            import copy

            pipeline_template = DatabaseService._get_aggregation_by_name(
                "TOP_COUNTRIES_BY_ARTICLES"
            )
            pipeline = copy.deepcopy(pipeline_template)
            pipeline[0]["$match"] = match_stage if match_stage else {}
            pipeline[-1]["$limit"] = limit
            results = DatabaseService.aggregate_articles(pipeline)
            for result in results:
                result["name"] = get_country_name(result["code"])
                result["iso2"] = result["code"]
            return results
        except Exception as e:
            logger.error(f"Error in get_top_countries_by_articles: {str(e)}")
            return []

    @staticmethod
    def get_global_statistics() -> dict:
        """Get global statistics about articles."""
        try:
            import copy

            total_pipeline = copy.deepcopy(
                DatabaseService._get_aggregation_by_name("GLOBAL_STATISTICS_TOTAL")
            )
            total_result = DatabaseService.aggregate_articles(total_pipeline)
            total_articles = total_result[0]["total"] if total_result else 0
            country_pipeline = copy.deepcopy(
                DatabaseService._get_aggregation_by_name("GLOBAL_STATISTICS_COUNTRIES")
            )
            countries = DatabaseService.aggregate_articles(country_pipeline)
            formatted_countries = []
            for country in countries:
                country_name = get_country_name(country["code"])
                if country_name:
                    formatted_country = {
                        "id": country["code"],
                        "code": country["code"],
                        "iso2": country["code"],
                        "name": country_name,
                        "value": country["value"],
                        "averageTone": country["averageTone"],
                    }
                    formatted_countries.append(formatted_country)
            return {
                "totalArticles": total_articles,
                "countries": formatted_countries,
                "averagePerCountry": (
                    total_articles / len(formatted_countries) if formatted_countries else 0
                ),
            }
        except Exception as e:
            logger.error(f"Error getting global statistics: {str(e)}")
            return {"totalArticles": 0, "countries": [], "averagePerCountry": 0}

    @staticmethod
    def get_country_details(country_code: str) -> Optional[dict]:
        """Get detailed information about a specific country."""
        try:
            import copy

            pipeline = copy.deepcopy(DatabaseService._get_aggregation_by_name("COUNTRY_DETAILS"))
            pipeline[0]["$match"]["sourceCountry"] = country_code
            results = DatabaseService.aggregate_articles(pipeline)
            country_name = get_country_name(country_code)
            if not country_name:
                return None
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
            match_stage: Dict[str, Any] = {"sourceCountry": country_code}
            start = DatabaseService._ensure_timezone_aware(start_date)
            end = DatabaseService._ensure_timezone_aware(end_date)
            if start or end:
                date_filter: Dict[str, Any] = {}
                if start:
                    date_filter["$gte"] = start.isoformat()
                if end:
                    date_filter["$lte"] = end.isoformat()
                if date_filter:
                    match_stage["date.isoDate"] = date_filter
            import copy

            timeline_pipeline = copy.deepcopy(
                DatabaseService._get_aggregation_by_name("COUNTRY_TIME_STATS_TIMELINE")
            )
            timeline_pipeline[0]["$match"] = match_stage
            timeline_data = DatabaseService.aggregate_articles(timeline_pipeline)
            formatted_timeline_data = []
            for item in timeline_data:
                try:
                    formatted_item = {
                        "date": item["date"],
                        "count": int(item["count"]),
                        "tone": float(item.get("tone", 0)),
                    }
                    formatted_timeline_data.append(formatted_item)
                except Exception as e:
                    logger.error(f"Error formatting timeline item {item}: {str(e)}")
            stats_pipeline = copy.deepcopy(
                DatabaseService._get_aggregation_by_name("COUNTRY_TIME_STATS_STATS")
            )
            stats_pipeline[0]["$match"] = match_stage
            
            # Add stages to ensure unique articles by title
            stats_pipeline.insert(1, {
                "$group": {
                    "_id": "$pageTitle",
                    "doc": { "$first": "$$ROOT" }
                }
            })
            stats_pipeline.insert(2, {
                "$replaceRoot": { "newRoot": "$doc" }
            })
            
            stats_results = DatabaseService.aggregate_articles(stats_pipeline)
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
            tf1_start = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe1_start))
            tf1_end = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe1_end))
            tf2_start = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe2_start))
            tf2_end = cast(datetime, DatabaseService._ensure_timezone_aware(timeframe2_end))
            import copy

            pipeline_template = DatabaseService._get_aggregation_by_name("COMPARE_TIME_PERIODS")

            def get_timeframe_data(start_date: datetime, end_date: datetime) -> dict:
                start_iso = start_date.isoformat()
                end_iso = end_date.isoformat()
                pipeline = copy.deepcopy(pipeline_template)
                pipeline[0]["$match"]["date.isoDate"]["$gte"] = start_iso
                pipeline[0]["$match"]["date.isoDate"]["$lte"] = end_iso
                results = DatabaseService.aggregate_articles(pipeline)
                total_articles = sum(day["articleCount"] for day in results)
                return {
                    "startDate": start_iso,
                    "endDate": end_iso,
                    "articleCount": total_articles,
                    "dailyData": results,
                }

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
            
    @staticmethod
    def get_daily_country_averages() -> dict:
        """Get daily average of articles for top and bottom countries."""
        try:
            # Get the pipeline from AGGREGATIONS
            pipeline = DatabaseService._get_aggregation_by_name("DAILY_COUNTRY_AVERAGES")
            results = DatabaseService.aggregate_articles(pipeline)
            
            # Convert country codes to names and filter out zero averages
            formatted_results = []
            for result in results:
                country_name = get_country_name(result["country"])
                if country_name and result["averageArticles"] > 0:
                    result["name"] = country_name
                    formatted_results.append(result)
            
            # Sort for highest and lowest
            sorted_results = sorted(formatted_results, key=lambda x: x["averageArticles"], reverse=True)
            highest = sorted_results[:7]
            lowest = sorted_results[-7:] if len(sorted_results) >= 7 else sorted_results
            lowest.reverse()  # Make it ascending order
            
            return {
                "highest": highest,
                "lowest": lowest
            }

        except Exception as e:
            logger.error(f"Error getting daily country averages: {str(e)}")
            return {
                "highest": [],
                "lowest": []
            }
