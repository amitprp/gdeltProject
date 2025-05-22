from fastapi import APIRouter, HTTPException
from typing import List, Literal, Optional
from ...services.gdelt_service import GdeltService
from ...services.source_analysis_service import SourceAnalysisService
# from ...services.db_service import DatabaseService
from ...services.file_db_service import FileDBService
from ...models.article import Article, HistoricalData, RealtimeData, CountryData
from ...models.source_analysis import (
    SourceAnalysisResponse,
    SourceAnalysisFilters,
    GroupedSourceResponse
)
from datetime import datetime
from pydantic import BaseModel
from ...utils.date_utils import validate_date_range
import logging
from ...utils.country_utils import get_country_name

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
gdelt_service = GdeltService()
source_analysis_service = SourceAnalysisService()
file_db_service = FileDBService()

@router.get("/articles/recent", response_model=List[Article])
async def get_recent_articles(days: int = 3):
    """Get recent antisemitic articles from the last N days."""
    if days < 0:
        raise HTTPException(status_code=422, detail="days must be positive")
    try:
        articles = await gdelt_service.get_antisemitic_articles(days)
        return articles
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/articles/realtime", response_model=RealtimeData)
async def get_realtime_data():
    """Get real-time article data and sentiment analysis."""
    try:
        data = await gdelt_service.get_realtime_mentions()
        return data
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/articles/historical", response_model=HistoricalData)
async def get_historical_data(days: int = 90, interval: str = "day"):
    """Get historical data for trend analysis."""
    if days < 0:
        raise HTTPException(status_code=422, detail="days must be positive")
    
    valid_intervals = ["hour", "day", "week", "month"]
    if interval not in valid_intervals:
        raise HTTPException(
            status_code=422,
            detail=f"interval must be one of: {', '.join(valid_intervals)}"
        )
    
    try:
        data = await gdelt_service.get_historical_data(days)
        return data
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/sources/analysis", response_model=SourceAnalysisResponse)
async def get_source_analysis(filters: SourceAnalysisFilters):
    """Get analysis of news sources with antisemitic content."""

    try:
        sources = await source_analysis_service.get_source_statistics(
            start_date=filters.startDate,
            end_date=filters.endDate,
            country=filters.country,
            author=filters.author
        )
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources/grouped", response_model=GroupedSourceResponse)
async def get_grouped_sources(
    group_by: Literal["author", "country"],
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    """Get articles grouped by author or country."""
    try:
        # Validate date range
        is_valid, error_message = validate_date_range(start_date, end_date)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)

        sources = await source_analysis_service.get_grouped_statistics(
            group_by=group_by,
            start_date=start_date,
            end_date=end_date
        )
        return {"groups": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/articles/top-countries", response_model=List[CountryData])
async def get_top_countries(
    limit: int = 10,
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    """Get top countries by number of antisemitic articles."""
    try:
        countries = await file_db_service.get_top_countries_by_articles(limit)
        return countries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/articles/global-stats")
async def get_global_stats():
    """Get global statistics about antisemitic articles."""
    try:
        stats = await file_db_service.get_global_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/articles/country/{country_code}")
async def get_country_details(country_code: str):
    """Get detailed information about a specific country."""
    try:
        country_data = await file_db_service.get_country_details(country_code)
        
        # If no data found, return empty stats with country info
        if not country_data:
            country_name = get_country_name(country_code)
            if not country_name:
                # Only throw 404 if the country code is invalid
                raise HTTPException(status_code=404, detail="Country not found")
            
            # Return empty stats for valid country with no articles
            return {
                "code": country_code,
                "name": country_name,
                "value": 0,
                "averageTone": 0,
                "iso2": country_code
            }
            
        return country_data
    except Exception as e:
        logger.error(f"Error in get_country_details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/articles/country/{country_code}/time-stats")
async def get_country_time_stats(
    country_code: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get time-based statistics for a specific country."""
    try:
        # Validate date range
        is_valid, error_message = validate_date_range(start_date, end_date)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error_message
            )

        stats = await file_db_service.get_country_time_stats(
            country_code,
            start_date=start_date,
            end_date=end_date
        )
        return stats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_country_time_stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching country statistics"
        )

class TimeFrameRequest(BaseModel):
    timeframe1_start: datetime
    timeframe1_end: datetime
    timeframe2_start: datetime
    timeframe2_end: datetime

@router.post("/articles/compare-trends")
async def compare_trends(request: TimeFrameRequest):
    """Compare article trends between two time periods."""
    try:
        # Validate first time frame
        is_valid, error_message = validate_date_range(
            request.timeframe1_start,
            request.timeframe1_end
        )
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid first time frame: {error_message}"
            )

        # Validate second time frame
        is_valid, error_message = validate_date_range(
            request.timeframe2_start,
            request.timeframe2_end
        )
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid second time frame: {error_message}"
            )

        comparison = await file_db_service.compare_time_periods(
            request.timeframe1_start,
            request.timeframe1_end,
            request.timeframe2_start,
            request.timeframe2_end
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
