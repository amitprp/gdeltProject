from datetime import datetime
from typing import List, Optional, Literal
from .file_db_service import FileDBService
import logging
import traceback

# Configure logging
logger = logging.getLogger(__name__)

class SourceAnalysisService:
    def __init__(self):
        self.db_service = FileDBService()

    async def get_source_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        country: Optional[str] = None,
        author: Optional[str] = None,
    ) -> List[dict]:
        """Get statistics about news sources and their antisemitic content."""
        try:
            logger.info(f"Getting source statistics - country: {country}, author: {author}, start_date: {start_date}, end_date: {end_date}")
            
            articles = await self.db_service.get_articles_by_source(
                country=country,
                author=author,
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info(f"Found {len(articles)} articles matching the criteria")
            
            # Process the articles to get statistics
            if not articles:
                return []
                
            # Group by source and country
            sources = {}
            for idx, article in enumerate(articles):
                try:
                    # Handle pageAuthors being either a string, list, or None
                    page_authors = article.get("pageAuthors")
                    
                    # Handle all possible cases for page_authors
                    if page_authors is None:
                        author_key = "Unknown"
                    elif isinstance(page_authors, list):
                        # Filter out None/empty values and join non-empty authors
                        valid_authors = [author for author in page_authors if author]
                        author_key = ", ".join(valid_authors) if valid_authors else "Unknown"
                    elif isinstance(page_authors, str):
                        author_key = page_authors if page_authors.strip() else "Unknown"
                    else:
                        # Handle any other unexpected type
                        author_key = "Unknown"
                        logger.warning(f"Unexpected pageAuthors type: {type(page_authors)} for article {idx}")
                        
                    source_key = (author_key, article.get("sourceCountry"))
                    if source_key not in sources:
                        sources[source_key] = {
                            "source": author_key,
                            "country": source_key[1] or "Unknown",
                            "articleCount": 0,
                            "totalTone": 0,
                            "lastArticleDate": None,
                            "articles": []
                        }
                    
                    source_data = sources[source_key]
                    source_data["articleCount"] += 1
                    
                    # Safely get tone value with default of 0
                    tone = article.get("tones", {}).get("overall", 0) or 0
                    source_data["totalTone"] += tone
                    
                    article_date = article.get("date", {}).get("isoDate")
                    
                    if article_date:
                        if not source_data["lastArticleDate"] or article_date > source_data["lastArticleDate"]:
                            source_data["lastArticleDate"] = article_date
                            
                    source_data["articles"].append({
                        "title": article.get("pageTitle", "No Title"),
                        "url": article.get("pageUrl", "#"),
                        "date": article.get("date", {}).get("isoDate", datetime.now().isoformat()),
                        "tone": tone
                    })
                except Exception as e:
                    logger.error(f"Error processing article {idx}: {str(e)}")
                    logger.error(f"Article data: {article}")
                    continue
            
            # Format the results
            results = []
            for source_key, source_data in sources.items():
                try:
                    if source_data["articleCount"] > 0:  # Prevent division by zero
                        results.append({
                            "source": source_data["source"],
                            "country": source_data["country"],
                            "articleCount": source_data["articleCount"],
                            "averageTone": source_data["totalTone"] / source_data["articleCount"],
                            "lastArticleDate": source_data["lastArticleDate"] or datetime.now().isoformat(),
                            "recentArticles": sorted(
                                source_data["articles"],
                                key=lambda x: x["date"],
                                reverse=True
                            )[:5]
                        })
                except Exception as e:
                    logger.error(f"Error processing source {source_key}: {str(e)}")
                    continue
            
            sorted_results = sorted(results, key=lambda x: x["articleCount"], reverse=True)
            logger.info(f"Successfully processed and returning {len(sorted_results)} source statistics")
            return sorted_results
            
        except Exception as e:
            logger.error(f"Error in get_source_statistics: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    async def get_grouped_statistics(
        self,
        group_by: Literal["author", "country"],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """Get articles grouped by author or country with statistics."""
        group_field = "pageAuthors" if group_by == "author" else "sourceCountry"
        
        return await self.db_service.get_grouped_articles(
            group_field=group_field,
            start_date=start_date,
            end_date=end_date
        ) 