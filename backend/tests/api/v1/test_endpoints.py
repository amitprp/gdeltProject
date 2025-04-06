import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

def test_get_recent_articles(client: TestClient):
    response = client.get("/api/v1/articles/recent")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        article = data[0]
        assert "url" in article
        assert "title" in article
        assert "seendate" in article
        assert "sourcecountry" in article
        assert "tone" in article
        assert "domain" in article

def test_get_realtime_mentions(client: TestClient):
    response = client.get("/api/v1/articles/realtime")
    assert response.status_code == 200
    data = response.json()
    assert "total_mentions" in data
    assert "sentiment" in data
    assert "articles" in data
    assert isinstance(data["total_mentions"], int)
    assert isinstance(data["sentiment"], (int, float))
    assert isinstance(data["articles"], list)

def test_get_historical_data(client: TestClient):
    # Test with default parameters
    response = client.get("/api/v1/articles/historical")
    assert response.status_code == 200
    data = response.json()
    assert "timeline" in data
    assert "top_countries" in data
    assert "top_sources" in data
    assert isinstance(data["timeline"], list)
    assert isinstance(data["top_countries"], list)
    assert isinstance(data["top_sources"], list)

    if len(data["timeline"]) > 0:
        point = data["timeline"][0]
        assert "date" in point
        assert "count" in point

    if len(data["top_countries"]) > 0:
        country = data["top_countries"][0]
        assert "country" in country
        assert "count" in country

    if len(data["top_sources"]) > 0:
        source = data["top_sources"][0]
        assert "source" in source
        assert "count" in source

def test_invalid_parameters(client: TestClient):
    # Test invalid days parameter
    response = client.get("/api/v1/articles/historical", params={"days": -1})
    assert response.status_code == 422

    # Test invalid interval parameter
    response = client.get("/api/v1/articles/historical", params={"interval": "invalid"})
    assert response.status_code == 422
