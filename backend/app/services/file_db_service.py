import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import os
from pathlib import Path
from ..utils.country_utils import get_country_name
import logging

# Configure logging
logger = logging.getLogger(__name__)

class FileDBService:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent / "core"
        self.articles_file = self.base_path / "articles.json"
        self.events_file = self.base_path / "events.json"
        self._cached_articles = None
        self._last_fetch_time = None
        self._cache_duration = 1400 * 60  # Cache duration in seconds

    async def _read_json_file(self, file_path: Path) -> List[dict]:
        """Read and parse a JSON file."""
        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return []
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return []

    async def _get_cached_articles(self, force_refresh: bool = False) -> List[dict]:
        """
        Get articles from cache or read from file if cache is expired or force refresh is requested.
        
        Args:
            force_refresh: If True, forces a cache refresh regardless of expiration
        """
        try:
            current_time = datetime.now().timestamp()
            
            # Check if we need to refresh the cache
            should_refresh = (
                force_refresh or
                self._cached_articles is None or
                self._last_fetch_time is None or
                current_time - self._last_fetch_time > self._cache_duration
            )
            
            if should_refresh:
                logger.info("Refreshing articles cache...")
                self._cached_articles = await self._read_json_file(self.articles_file)
                self._last_fetch_time = current_time
                logger.info(f"Cache refreshed with {len(self._cached_articles)} articles")
            
            return self._cached_articles or []
        except Exception as e:
            logger.error(f"Error getting cached articles: {str(e)}")
            return []

    async def refresh_cache(self) -> bool:
        """
        Force refresh the articles cache.
        Returns True if refresh was successful, False otherwise.
        """
        try:
            await self._get_cached_articles(force_refresh=True)
            return True
        except Exception as e:
            logger.error(f"Error refreshing cache: {str(e)}")
            return False

    async def get_articles_with_filters(
        self,
        match_conditions: Dict[str, Any]
    ) -> List[dict]:
        """Get articles matching the filter conditions."""
        articles = await self._get_cached_articles()
        
        def matches_conditions(article: dict) -> bool:
            for key, value in match_conditions.items():
                if key == "date.isoDate":
                    article_date = datetime.fromisoformat(article["date"]["isoDate"].replace('Z', '+00:00'))
                    if isinstance(value, dict):
                        if "$gte" in value and article_date < value["$gte"]:
                            return False
                        if "$lte" in value and article_date > value["$lte"]:
                            return False
                elif key == "sourceCountry" and article.get(key) != value:
                    return False
                elif key == "pageAuthors":
                    article_authors = article.get(key)
                    if article_authors is None:
                        return False
                    if isinstance(article_authors, list):
                        # Case-insensitive comparison for author list
                        if not any(author.lower() == value.lower() for author in article_authors):
                            return False
                    elif article_authors.lower() != value.lower():  # Case-insensitive comparison for single author
                        return False
            return True

        return [article for article in articles if matches_conditions(article)]

    async def aggregate_articles(
        self,
        pipeline: List[Dict[str, Any]]
    ) -> List[dict]:
        """Process articles through an aggregation pipeline."""
        articles = await self._get_cached_articles()
        results = articles

        for stage in pipeline:
            if "$match" in stage:
                results = await self.get_articles_with_filters(stage["$match"])
            
            elif "$group" in stage:
                grouped = {}
                group_config = stage["$group"]
                id_field = group_config["_id"].replace("$", "")
                
                for article in results:
                    key = article.get(id_field)
                    if key not in grouped:
                        grouped[key] = {
                            "_id": key,
                            "articleCount": 0,
                            "averageTone": 0,
                            "totalTone": 0,
                            "lastArticleDate": None,
                            "articles": []
                        }
                    
                    group = grouped[key]
                    group["articleCount"] += 1
                    group["totalTone"] += article.get("tones", {}).get("overall", 0)
                    article_date = article.get("date", {}).get("isoDate")
                    if article_date:
                        if not group["lastArticleDate"] or article_date > group["lastArticleDate"]:
                            group["lastArticleDate"] = article_date
                    
                    group["articles"].append({
                        "title": article.get("pageTitle"),
                        "url": article.get("pageUrl"),
                        "date": article.get("date", {}).get("isoDate"),
                        "tone": article.get("tones", {}).get("overall", 0)
                    })
                
                results = []
                for group in grouped.values():
                    if group["articleCount"] > 0:
                        group["averageTone"] = group["totalTone"] / group["articleCount"]
                    results.append(group)
            
            elif "$project" in stage:
                project_config = stage["$project"]
                projected = []
                for item in results:
                    new_item = {}
                    for new_field, value in project_config.items():
                        if new_field == "_id":
                            continue
                        elif new_field == "name":
                            new_item[new_field] = item["_id"]
                        elif isinstance(value, dict) and "$slice" in value:
                            field_name = value["$slice"][0]
                            slice_count = value["$slice"][1]
                            new_item[new_field] = item[field_name.replace("$", "")][:slice_count]
                        elif value == 1:
                            new_item[new_field] = item[new_field]
                    projected.append(new_item)
                results = projected
            
            elif "$sort" in stage:
                sort_config = stage["$sort"]
                for field, direction in sort_config.items():
                    results.sort(key=lambda x: x[field], reverse=(direction == -1))
            
            elif "$match" in stage and "name" in stage["$match"]:
                results = [r for r in results if r.get("name") is not None]

        return results

    async def get_articles_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get articles within a date range."""
        match_conditions = {}
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            match_conditions["date.isoDate"] = date_filter
        
        return await self.get_articles_with_filters(match_conditions)

    async def get_articles_by_source(
        self,
        country: Optional[str] = None,
        author: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get articles filtered by source attributes."""
        match_conditions = {}
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            match_conditions["date.isoDate"] = date_filter
            
        if country:
            match_conditions["sourceCountry"] = country
            
        if author:
            match_conditions["pageAuthors"] = author
            
        return await self.get_articles_with_filters(match_conditions)

    async def get_grouped_articles(
        self,
        group_field: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get articles grouped by a specific field with statistics."""
        match_pipeline = {}
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            match_pipeline["date.isoDate"] = date_filter

        articles = await self._get_cached_articles()
        
        # Filter articles by date if needed
        filtered_articles = []
        for article in articles:
            include = True
            if start_date or end_date:
                article_date = datetime.fromisoformat(article["date"]["isoDate"].replace('Z', '+00:00'))
                if start_date and article_date < start_date:
                    include = False
                if end_date and article_date > end_date:
                    include = False
            if include:
                filtered_articles.append(article)

        # Group articles
        grouped = {}
        for article in filtered_articles:
            # Handle the grouping field value
            if group_field == "pageAuthors":
                authors = article.get(group_field)
                # Handle different author formats
                if authors is None:
                    continue  # Skip articles with no authors
                elif isinstance(authors, list):
                    # If it's a list of authors, create an entry for each author
                    for author in authors:
                        if not author:  # Skip empty author names
                            continue
                        self._update_group_data(grouped, author, article)
                    continue  # Skip the rest since we've handled all authors
                elif isinstance(authors, str) and authors.strip():
                    key = authors
                else:
                    continue  # Skip invalid author entries
            else:
                # For sourceCountry field
                key = article.get(group_field)
                if not key or key.strip() == "":
                    continue  # Skip entries with no country
                if group_field == "sourceCountry":
                    key = get_country_name(key)  # Convert country code to name
            
            self._update_group_data(grouped, key, article)

        # Format results
        results = []
        for key, data in grouped.items():
            if data["articleCount"] > 0:
                results.append({
                    "name": key,
                    "articleCount": data["articleCount"],
                    "averageTone": data["totalTone"] / data["articleCount"],
                    "lastArticleDate": data["lastArticleDate"] or datetime.now().isoformat(),
                    "recentArticles": sorted(
                        data["articles"],
                        key=lambda x: x["date"],
                        reverse=True
                    )[:5]
                })

        # Sort by article count in descending order
        results.sort(key=lambda x: x["articleCount"], reverse=True)
        return results

    def _update_group_data(self, grouped: dict, key: str, article: dict) -> None:
        """Helper method to update the grouped data structure."""
        if key not in grouped:
            grouped[key] = {
                "articleCount": 0,
                "totalTone": 0,
                "lastArticleDate": None,
                "articles": []
            }
        
        group = grouped[key]
        group["articleCount"] += 1
        group["totalTone"] += article.get("tones", {}).get("overall", 0) or 0
        
        article_date = article.get("date", {}).get("isoDate")
        if article_date:
            if not group["lastArticleDate"] or article_date > group["lastArticleDate"]:
                group["lastArticleDate"] = article_date
        
        group["articles"].append({
            "title": article.get("pageTitle", "No Title"),
            "url": article.get("pageUrl", "#"),
            "date": article.get("date", {}).get("isoDate", ""),
            "tone": article.get("tones", {}).get("overall", 0) or 0
        })

    async def get_top_countries_by_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the top countries by number of articles."""
        try:
            articles = await self._get_cached_articles()
            
            # Count articles by country
            country_counts = {}
            for article in articles:
                country_code = article.get("sourceCountry")
                if not country_code:
                    continue
                
                if country_code not in country_counts:
                    country_counts[country_code] = {
                        "code": country_code,
                        "name": get_country_name(country_code),
                        "value": 0,
                    }
                
                country_data = country_counts[country_code]
                country_data["value"] += 1
            
            # Calculate average tone and format results
            results = []
            for country_data in country_counts.values():
                if country_data["value"] > 0:
                    results.append(country_data)
            
            # Sort by article count (value) in descending order and take top N
            results.sort(key=lambda x: x["value"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            print(f"Error getting top countries: {str(e)}")
            return []

    async def get_global_statistics(self) -> dict:
        """Get global statistics about articles."""
        try:
            articles = await self._get_cached_articles()
            logger.info(f"Calculating global statistics from {len(articles)} articles")
            
            # Count articles by country
            country_stats = {}
            for article in articles:
                country_code = article.get("sourceCountry")
                if not country_code:
                    continue
                
                if country_code not in country_stats:
                    country_stats[country_code] = {
                        "code": country_code,
                        "name": get_country_name(country_code),
                        "value": 0,
                        "totalTone": 0
                    }
                
                stats = country_stats[country_code]
                stats["value"] += 1
                stats["totalTone"] += article.get("tones", {}).get("overall", 0) or 0
            
            # Calculate averages and format results
            countries = []
            total_articles = 0
            for stats in country_stats.values():
                if stats["value"] > 0:
                    stats["averageTone"] = stats["totalTone"] / stats["value"]
                    del stats["totalTone"]
                    countries.append(stats)
                    total_articles += stats["value"]
            
            # Sort countries by article count
            countries.sort(key=lambda x: x["value"], reverse=True)
            
            result = {
                "totalArticles": total_articles,
                "countries": countries,
                "averagePerCountry": total_articles / len(countries) if countries else 0
            }
            
            logger.info(f"Global statistics calculated: {total_articles} total articles across {len(countries)} countries")
            return result
            
        except Exception as e:
            logger.error(f"Error getting global statistics: {str(e)}")
            return {
                "totalArticles": 0,
                "countries": [],
                "averagePerCountry": 0
            }

    async def get_country_details(self, country_code: str) -> Optional[dict]:
        """Get detailed information about a specific country."""
        try:
            articles = await self._get_cached_articles()
            logger.info(f"Getting details for country: {country_code}")
            
            # Filter articles for this country
            country_articles = [
                article for article in articles 
                if article.get("sourceCountry") == country_code
            ]
            
            if not country_articles:
                logger.warning(f"No articles found for country: {country_code}")
                return None
            
            # Calculate statistics
            total_articles = len(country_articles)
            total_tone = sum(article.get("tones", {}).get("overall", 0) for article in country_articles)
            average_tone = total_tone / total_articles if total_articles > 0 else 0
            
            return {
                "code": country_code,
                "name": get_country_name(country_code),
                "value": total_articles,
                "averageTone": average_tone,
                "iso2": country_code
            }
        except Exception as e:
            logger.error(f"Error getting country details: {str(e)}")
            return None

    def make_timezone_aware(self, dt: datetime) -> datetime:
        """Convert naive datetime to UTC timezone-aware datetime."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    async def get_country_time_stats(
        self,
        country_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get time-based statistics for a specific country."""
        try:
            articles = await self._get_cached_articles()
            
            # Ensure dates are timezone-aware
            if start_date:
                start_date = self.make_timezone_aware(start_date)
            if end_date:
                end_date = self.make_timezone_aware(end_date)
            
            # Filter articles for this country and date range
            country_articles = []
            timeline_data = {}
            
            for article in articles:
                if article.get("sourceCountry") != country_code:
                    continue
                    
                try:
                    # Parse the ISO date and ensure it's timezone-aware
                    article_date = datetime.fromisoformat(
                        article["date"]["isoDate"].replace('Z', '+00:00')
                    )
                    article_date = self.make_timezone_aware(article_date)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid date format in article: {article.get('date', {})}. Error: {str(e)}")
                    continue
                
                if start_date and article_date < start_date:
                    continue
                if end_date and article_date > end_date:
                    continue
                
                country_articles.append(article)
                
                # Group by date for timeline
                date_key = article_date.strftime("%Y-%m-%d")
                if date_key not in timeline_data:
                    timeline_data[date_key] = {"count": 0, "total_tone": 0}
                
                timeline_data[date_key]["count"] += 1
                timeline_data[date_key]["total_tone"] += article.get("tones", {}).get("overall", 0) or 0
            
            # Calculate statistics
            total_articles = len(country_articles)
            total_tone = sum(article.get("tones", {}).get("overall", 0) or 0 for article in country_articles)
            average_tone = total_tone / total_articles if total_articles > 0 else 0
            
            # Format timeline data
            timeline = [
                {
                    "date": date,
                    "count": data["count"],
                    "tone": data["total_tone"] / data["count"] if data["count"] > 0 else 0
                }
                for date, data in sorted(timeline_data.items())
            ]
            
            # Get recent articles
            recent_articles = sorted(
                country_articles,
                key=lambda x: x["date"]["isoDate"],
                reverse=True
            )[:10]  # Get top 10 most recent
            
            formatted_articles = [
                {
                    "title": article.get("pageTitle", "No Title"),
                    "url": article.get("pageUrl", "#"),
                    "date": article["date"]["isoDate"],
                    "source": article.get("pageAuthors", "Unknown Source")
                }
                for article in recent_articles
            ]
            
            return {
                "articleCount": total_articles,
                "averageTone": average_tone,
                "timelineData": timeline,
                "articles": formatted_articles
            }
            
        except Exception as e:
            logger.error(f"Error getting country time stats: {str(e)}")
            return {
                "articleCount": 0,
                "averageTone": 0,
                "timelineData": [],
                "articles": []
            }

    async def compare_time_periods(
        self,
        timeframe1_start: datetime,
        timeframe1_end: datetime,
        timeframe2_start: datetime,
        timeframe2_end: datetime
    ) -> List[dict]:
        """Compare article trends between two time periods."""
        try:
            articles = await self._get_cached_articles()
            
            async def get_timeframe_data(start_date: datetime, end_date: datetime) -> dict:
                # Filter articles for this timeframe
                timeframe_articles = [
                    article for article in articles
                    if start_date <= datetime.fromisoformat(article["date"]["isoDate"].replace('Z', '+00:00')) <= end_date
                ]
                
                # Group by date
                daily_data = {}
                for article in timeframe_articles:
                    article_date = datetime.fromisoformat(article["date"]["isoDate"].replace('Z', '+00:00'))
                    date_key = article_date.strftime("%Y-%m-%d")
                    
                    if date_key not in daily_data:
                        daily_data[date_key] = {
                            "date": date_key,
                            "articleCount": 0,
                            "totalTone": 0
                        }
                    
                    daily_data[date_key]["articleCount"] += 1
                    daily_data[date_key]["totalTone"] += article.get("tones", {}).get("overall", 0)
                
                # Calculate averages and sort by date
                daily_stats = []
                for stats in daily_data.values():
                    if stats["articleCount"] > 0:
                        stats["averageTone"] = stats["totalTone"] / stats["articleCount"]
                        del stats["totalTone"]
                        daily_stats.append(stats)
                
                daily_stats.sort(key=lambda x: x["date"])
                
                return {
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "articleCount": sum(day["articleCount"] for day in daily_stats),
                    "dailyData": daily_stats
                }
            
            # Get data for both timeframes
            timeframe1_data = await get_timeframe_data(timeframe1_start, timeframe1_end)
            timeframe2_data = await get_timeframe_data(timeframe2_start, timeframe2_end)
            
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