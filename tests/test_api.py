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


def test_api_ledger_transactions():
    # Unfiltered transactions
    res = client.get("/api/ledger/transactions?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

    # Filtered by commodity
    res_comm = client.get("/api/ledger/transactions?commodity=udu&limit=5")
    assert res_comm.status_code == 200
    assert isinstance(res_comm.json(), list)

    # Filtered by officer
    res_off = client.get("/api/ledger/transactions?officer=ab-ba-sa6-ga&limit=5")
    assert res_off.status_code == 200
    assert isinstance(res_off.json(), list)


def test_api_tablets_advanced_filters():
    # Filter by period
    res_period = client.get("/api/tablets?period=Ur%20III&limit=5")
    assert res_period.status_code == 200
    data_period = res_period.json()
    assert "items" in data_period

    # Filter by has_date
    res_date = client.get("/api/tablets?has_date=true&limit=5")
    assert res_date.status_code == 200

    # Search filter
    res_search = client.get("/api/tablets?search=P100001&limit=5")
    assert res_search.status_code == 200


def test_api_search_kmer():
    res = client.get("/api/search?q=udu&mode=kmer&limit=5")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_graph_view_html():
    res = client.get("/api/graph/view")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "<!DOCTYPE html>" in res.text or "<html" in res.text


def test_api_explorer_html():
    res = client.get("/explorer")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "<!DOCTYPE html>" in res.text or "<html" in res.text

    # Test redirect /browser -> /explorer
    res_redir = client.get("/browser", follow_redirects=False)
    assert res_redir.status_code in (307, 302, 308, 301)


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


def test_api_category_filter():
    for cat in ["showcase", "scribes", "dates", "joins", "transactions"]:
        res = client.get(f"/api/tablets?category={cat}&limit=5")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert len(data["items"]) > 0


def test_api_metrology_parsing():
    from src.ledger.metrology import MetrologyEngine

    engine = MetrologyEngine()

    # Test capacity parsing
    lines = [
        {"line_number": "1", "raw_text": "2(barig) 3(ban2) sze gur"},
        {"line_number": "2", "raw_text": "5(disz) gin2 ku3-babbar"},
        {"line_number": "3", "raw_text": "10(disz) udu"},
    ]
    res = engine.parse_tablet_metrology(lines)
    assert len(res) == 3

    types = [r["type"] for r in res]
    assert "Capacity (Volume)" in types
    assert "Weight (Mass)" in types
    assert "Discrete Count" in types


def test_api_official_search_and_source_link():
    # Test searching for an official name in ledger
    res = client.get("/api/tablets?search=ab-ba-sa6-ga&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) > 0

    # Test tablet detail source URL
    res_det = client.get("/api/tablets/P100001")
    assert res_det.status_code == 200
    det = res_det.json()
    assert "photos" in det
    assert "source_url" in det["photos"]
    assert "cdli.mpiwg-berlin.mpg.de/artifacts" in det["photos"]["source_url"]



