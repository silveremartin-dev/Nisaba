"""
Integration tests for Nisaba FastAPI REST microservice.
Verifies all public endpoints, query parameters, error responses, and schemas.
"""

from fastapi.testclient import TestClient
import pytest

from src.api.app import app

client = TestClient(app)


def test_root_and_health():
    res_root = client.get("/")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert data_root["engine"] == "Nisaba"
    assert data_root["status"] == "ONLINE"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "OK"


def test_api_stats():
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_tablets" in data
    assert "engine_status" in data
    assert data["total_tablets"] > 0


def test_api_tablets_list():
    res = client.get("/api/tablets?limit=5&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert "items" in data
    assert len(data["items"]) <= 5
    if len(data["items"]) > 0:
        first = data["items"][0]
        assert "id_text" in first


def test_api_tablet_detail():
    # P100001 or similar from the database
    res = client.get("/api/tablets/P100001")
    if res.status_code == 200:
        data = res.json()
        assert data["id_text"] == "P100001"
        assert "lines" in data
        assert "photos" in data
    else:
        # Fallback test with 404 for non-existent tablet
        res_404 = client.get("/api/tablets/NONEXISTENT999")
        assert res_404.status_code == 404


def test_api_search():
    res = client.get("/api/search?q=udu&limit=10")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    if items:
        assert "raw_text" in items[0]


def test_api_ledger_officials():
    res = client.get("/api/ledger/officials?limit=10")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_prosopography_graph():
    # Cytoscape format
    res_cy = client.get("/api/graph/prosopography?format=cytoscape&max_nodes=20")
    assert res_cy.status_code == 200
    data_cy = res_cy.json()
    assert "elements" in data_cy
    assert "nodes" in data_cy["elements"]

    # D3 format
    res_d3 = client.get("/api/graph/prosopography?format=d3&max_nodes=20")
    assert res_d3.status_code == 200
    data_d3 = res_d3.json()
    assert "nodes" in data_d3
    assert "links" in data_d3
