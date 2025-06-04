from datetime import datetime
from typing import List, Optional, Literal
from .db.db_service import DatabaseService
import logging
import traceback

# Configure logging
logger = logging.getLogger(__name__)

class SourceAnalysisService:
    def __init__(self):
        self.db_service = DatabaseService()

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
            
            articles = self.db_service.get_articles_by_source(
                country=country,
                author=author,
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info(f"Found {len(articles)} articles matching the criteria")
            
            # Process the articles to get statistics
            if not articles:
                return []
            
            # The articles are already grouped and processed by the database service
            # Just need to ensure they're sorted by article count
            sorted_results = sorted(articles, key=lambda x: x["articleCount"], reverse=True)
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
        
        return self.db_service.get_grouped_articles(
            group_field=group_field,
            start_date=start_date,
            end_date=end_date
        ) 