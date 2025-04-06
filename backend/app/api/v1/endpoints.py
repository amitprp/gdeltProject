from fastapi import APIRouter, HTTPException
from typing import List
from ...services.gdelt_service import GdeltService
from ...models.article import Article, HistoricalData, RealtimeData

router = APIRouter()
gdelt_service = GdeltService()

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
