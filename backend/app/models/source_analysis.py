from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ArticleInfo(BaseModel):
    title: str
    url: str
    date: datetime
    tone: float

class SourceStatistics(BaseModel):
    source: str
    country: str
    articleCount: int
    averageTone: float
    lastArticleDate: datetime
    recentArticles: List[ArticleInfo]

class SourceAnalysisResponse(BaseModel):
    sources: List[SourceStatistics]

class GroupedSourceStatistics(BaseModel):
    name: str
    articleCount: int
    averageTone: float
    lastArticleDate: datetime
    recentArticles: List[ArticleInfo]

class GroupedSourceResponse(BaseModel):
    groups: List[GroupedSourceStatistics]

class SourceAnalysisFilters(BaseModel):
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    country: Optional[str] = None
    author: Optional[str] = None 