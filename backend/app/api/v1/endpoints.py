from fastapi import APIRouter, HTTPException
from typing import List, Literal, Optional
from ...services.source_analysis_service import SourceAnalysisService
from ...services.db_service import DatabaseService
from ...models.article import Article, HistoricalData, RealtimeData, CountryData
from ...models.source_analysis import (
    SourceAnalysisResponse,
    SourceAnalysisFilters,
    GroupedSourceResponse,
)
from datetime import datetime
from pydantic import BaseModel
from ...utils.date_utils import validate_date_range
import logging
from ...utils.country_utils import get_country_name

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

source_analysis_service = SourceAnalysisService()
database_service = DatabaseService()

@router.post("/sources/analysis", response_model=SourceAnalysisResponse)
async def get_source_analysis(filters: SourceAnalysisFilters):
    """Get analysis of news sources with antisemitic content."""

    try:
        
        sources = await source_analysis_service.get_source_statistics(
            start_date=filters.startDate,
            end_date=filters.endDate,
            country=filters.country,
            author=filters.author,
        )
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/grouped", response_model=GroupedSourceResponse)
async def get_grouped_sources(
    group_by: Literal["author", "country"],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """Get articles grouped by author or country."""
    try:
        sources = await source_analysis_service.get_grouped_statistics(
            group_by=group_by, start_date=start_date, end_date=end_date
        )
        return {"groups": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/top-countries", response_model=List[CountryData])
async def get_top_countries(
    limit: int = 10, start_date: datetime | None = None, end_date: datetime | None = None
):
    """Get top countries by number of antisemitic articles."""
    try:
        countries = database_service.get_top_countries_by_articles(limit)
        return countries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/global-stats")
async def get_global_stats():
    """Get global statistics about antisemitic articles."""
    try:
        stats = database_service.get_global_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/country/{country_code}")
async def get_country_details(country_code: str):
    """Get detailed information about a specific country."""
    try:
        country_data = database_service.get_country_details(country_code)
        country_name = get_country_name(country_code)

        # If no data found and country code is invalid, return 404
        if not country_data and not country_name:
            raise HTTPException(status_code=404, detail="Country not found")

        # If country exists but no data, return empty stats
        if not country_data and country_name:
            return {
                "code": country_code,
                "name": country_name,
                "value": 0,
                "averageTone": 0,
                "iso2": country_code,
            }

        return country_data
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error in get_country_details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/country/{country_code}/time-stats")
async def get_country_time_stats(
    country_code: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
):
    """Get time-based statistics for a specific country."""
    try:
        # Validate date range
        is_valid, error_message = validate_date_range(start_date, end_date)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)

        stats = database_service.get_country_time_stats(
            country_code, start_date=start_date, end_date=end_date
        )
        return stats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_country_time_stats: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching country statistics"
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
        # Log incoming request dates
        logger.info(f"Comparing time periods with dates: TF1({request.timeframe1_start} - {request.timeframe1_end}), TF2({request.timeframe2_start} - {request.timeframe2_end})")
        
        # Validate first time frame
        is_valid, error_message = validate_date_range(
            request.timeframe1_start, request.timeframe1_end
        )
        if not is_valid:
            logger.error(f"Invalid first time frame: {error_message}")
            raise HTTPException(
                status_code=400, detail=f"Invalid first time frame: {error_message}"
            )

        # Validate second time frame
        is_valid, error_message = validate_date_range(
            request.timeframe2_start, request.timeframe2_end
        )
        if not is_valid:
            logger.error(f"Invalid second time frame: {error_message}")
            raise HTTPException(
                status_code=400, detail=f"Invalid second time frame: {error_message}"
            )

        comparison = database_service.compare_time_periods(
            request.timeframe1_start,
            request.timeframe1_end,
            request.timeframe2_start,
            request.timeframe2_end,
        )
        
        # Log comparison results
        logger.info(f"Comparison results: TF1({comparison[0]['articleCount']} articles), TF2({comparison[1]['articleCount']} articles)")
        
        return comparison
    except Exception as e:
        logger.error(f"Error in compare_trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/daily-averages")
async def get_daily_averages():
    """Get daily average of articles for top countries."""
    try:
        stats = database_service.get_daily_country_averages()
        return stats
    except Exception as e:
        logger.error(f"Error in get_daily_averages: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching daily averages"
        )
