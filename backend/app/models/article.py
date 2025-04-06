from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime


class Article(BaseModel):
    url: str
    title: str
    seendate: str
    sourcecountry: Optional[str] = None
    tone: Optional[float] = None
    domain: Optional[str] = None
    
    @field_validator('seendate', mode='before')
    @classmethod
    def parse_seendate(cls, v):
        if isinstance(v, datetime):
            return v.strftime('%Y-%m-%dT%H:%M:%SZ')
        return v
    
    
class TimelinePoint(BaseModel):
    date: str
    count: int
    
    
class SourceCount(BaseModel):
    source: str
    count: int
    
    
class CountryCount(BaseModel):
    country: str
    count: int
    
    
class HistoricalData(BaseModel):
    timeline: List[TimelinePoint]
    top_sources: List[SourceCount]
    top_countries: List[CountryCount]
    
    
class RealtimeData(BaseModel):
    articles: List[Article]
    sentiment: float
    total_mentions: int
