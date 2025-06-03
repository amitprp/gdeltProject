import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.api.v1.endpoints import router
from unittest.mock import Mock, patch
from fastapi import HTTPException

# Create test client
client = TestClient(router)

# Mock data
mock_article = {
    "url": "https://test.com/article",
    "title": "Test Article",
    "seendate": "2024-08-20T00:00:00Z",
    "sourcecountry": "US",
    "tone": -5.49,
    "domain": "test.com"
}

mock_article_info = {
    "title": "Test Article",
    "url": "https://test.com/article",
    "date": "2024-08-20T00:00:00Z",
    "tone": -5.49
}

@pytest.fixture
def mock_gdelt_service():
    with patch("app.api.v1.endpoints.gdelt_service") as mock:
        async def mock_get_antisemitic_articles(*args, **kwargs):
            return [mock_article]
        async def mock_get_realtime_mentions(*args, **kwargs):
            return {
                "articles": [mock_article],
                "sentiment": -2.5,
                "total_mentions": 100
            }
        async def mock_get_historical_data(*args, **kwargs):
            return {
                "timeline": [
                    {
                        "date": datetime(2024, 1, 1),
                        "count": 10,
                        "tone": -2.0
                    }
                ],
                "top_sources": [],
                "top_countries": []
            }
        mock.get_antisemitic_articles = mock_get_antisemitic_articles
        mock.get_realtime_mentions = mock_get_realtime_mentions
        mock.get_historical_data = mock_get_historical_data
        yield mock

@pytest.fixture
def mock_source_analysis_service():
    with patch("app.api.v1.endpoints.source_analysis_service") as mock:
        async def mock_get_source_statistics(*args, **kwargs):
            # Return empty list for non-existent country or author
            if kwargs.get("country") == "XX" or kwargs.get("author") == "Non Existent":
                return []
            return [{
                "source": "test.com",
                "country": "US",
                "articleCount": 10,
                "averageTone": -2.0,
                "lastArticleDate": "2024-08-20T00:00:00Z",
                "recentArticles": [mock_article_info]
            }]
        async def mock_get_grouped_statistics(*args, **kwargs):
            # Return empty list when mock is configured to return empty results
            if getattr(mock.get_grouped_statistics, "return_value", None) == []:
                return []
            return [{
                "name": "Test Group",
                "articleCount": 10,
                "averageTone": -2.0,
                "lastArticleDate": "2024-08-20T00:00:00Z",
                "recentArticles": [mock_article_info]
            }]
        mock.get_source_statistics = mock_get_source_statistics
        mock.get_grouped_statistics = mock_get_grouped_statistics
        yield mock

@pytest.fixture
def mock_database_service():
    with patch("app.api.v1.endpoints.database_service") as mock:
        yield mock

def test_get_source_analysis_success(mock_source_analysis_service):
    request_data = {
        "startDate": "2024-01-01T00:00:00",
        "endDate": "2024-01-31T00:00:00",
        "country": "US",
        "author": "Test Author"
    }
    response = client.post("/sources/analysis", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert isinstance(data["sources"], list)

def test_get_source_analysis_empty_results(mock_source_analysis_service):
    mock_source_analysis_service.get_source_statistics.return_value = []
    request_data = {
        "startDate": "2024-01-01T00:00:00",
        "endDate": "2024-01-31T00:00:00",
        "country": "XX",  # Non-existent country
        "author": "Non Existent"
    }
    response = client.post("/sources/analysis", json=request_data)
    assert response.status_code == 200
    assert response.json()["sources"] == []

def test_get_source_analysis_special_characters(mock_source_analysis_service):
    request_data = {
        "startDate": "2024-01-01T00:00:00",
        "endDate": "2024-01-31T00:00:00",
        "country": "US",
        "author": "Test@#$%^&*()Author"  # Special characters in author name
    }
    response = client.post("/sources/analysis", json=request_data)
    assert response.status_code == 200
    assert "sources" in response.json()

def test_get_grouped_sources_success(mock_source_analysis_service):
    response = client.get("/sources/grouped?group_by=country")
    assert response.status_code == 200
    data = response.json()
    assert "groups" in data
    assert isinstance(data["groups"], list)

def test_get_grouped_sources_empty_results(mock_source_analysis_service):
    mock_source_analysis_service.get_grouped_statistics.return_value = []
    response = client.get("/sources/grouped?group_by=author")
    assert response.status_code == 200
    assert response.json()["groups"] == []

def test_get_top_countries_success(mock_database_service):
    mock_countries = [
        {
            "code": "US",
            "name": "United States",
            "value": 100,
            "averageTone": -2.0,
            "iso2": "US"
        }
    ]
    mock_database_service.get_top_countries_by_articles.return_value = mock_countries
    response = client.get("/articles/top-countries")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_top_countries_empty_results(mock_database_service):
    mock_database_service.get_top_countries_by_articles.return_value = []
    response = client.get("/articles/top-countries")
    assert response.status_code == 200
    assert response.json() == []

def test_get_top_countries_large_limit(mock_database_service):
    response = client.get("/articles/top-countries?limit=1000")
    assert response.status_code == 200

def test_get_global_stats_success(mock_database_service):
    mock_stats = {
        "totalArticles": 1000,
        "averageTone": -2.5,
        "countries": [],
        "averagePerCountry": 50
    }
    mock_database_service.get_global_statistics.return_value = mock_stats
    response = client.get("/articles/global-stats")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_get_global_stats_empty_data(mock_database_service):
    mock_stats = {
        "totalArticles": 0,
        "countries": [],
        "averagePerCountry": 0
    }
    mock_database_service.get_global_statistics.return_value = mock_stats
    response = client.get("/articles/global-stats")
    assert response.status_code == 200
    assert response.json()["totalArticles"] == 0

def test_get_country_details_success(mock_database_service):
    mock_data = {
        "code": "US",
        "name": "United States",
        "value": 100,
        "averageTone": -2.5,
        "iso2": "US"
    }
    mock_database_service.get_country_details.return_value = mock_data
    response = client.get("/articles/country/US")
    assert response.status_code == 200
    assert response.json() == mock_data

def test_get_country_details_empty_country_code(mock_database_service):
    response = client.get("/articles/country/")
    assert response.status_code == 404

def test_get_country_details_zero_articles(mock_database_service):
    mock_data = {
        "code": "US",
        "name": "United States",
        "value": 0,
        "averageTone": 0,
        "iso2": "US"
    }
    mock_database_service.get_country_details.return_value = mock_data
    response = client.get("/articles/country/US")
    assert response.status_code == 200
    assert response.json()["value"] == 0

def test_compare_trends_success(mock_database_service):
    mock_data = [
        {"articleCount": 10, "dailyData": []},
        {"articleCount": 20, "dailyData": []}
    ]
    mock_database_service.compare_time_periods.return_value = mock_data
    request_data = {
        "timeframe1_start": "2024-01-01T00:00:00",
        "timeframe1_end": "2024-01-31T00:00:00",
        "timeframe2_start": "2024-02-01T00:00:00",
        "timeframe2_end": "2024-02-29T00:00:00"
    }
    response = client.post("/articles/compare-trends", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["articleCount"] == 10
    assert data[1]["articleCount"] == 20

def test_compare_trends_overlapping_timeframes(mock_database_service):
    request_data = {
        "timeframe1_start": "2024-01-01T00:00:00",
        "timeframe1_end": "2024-02-15T00:00:00",
        "timeframe2_start": "2024-02-01T00:00:00",  # Overlaps with timeframe1
        "timeframe2_end": "2024-02-29T00:00:00"
    }
    response = client.post("/articles/compare-trends", json=request_data)
    assert response.status_code == 200  # Overlapping should be allowed

def test_compare_trends_empty_results(mock_database_service):
    mock_database_service.compare_time_periods.return_value = [
        {"articleCount": 0, "dailyData": []},
        {"articleCount": 0, "dailyData": []}
    ]
    request_data = {
        "timeframe1_start": "2024-01-01T00:00:00",
        "timeframe1_end": "2024-01-31T00:00:00",
        "timeframe2_start": "2024-02-01T00:00:00",
        "timeframe2_end": "2024-02-29T00:00:00"
    }
    response = client.post("/articles/compare-trends", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(period["articleCount"] == 0 for period in data) 