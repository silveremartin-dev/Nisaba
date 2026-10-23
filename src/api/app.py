"""
Nisaba REST API Microservice.
Exposes DuckDB analytical queries, full-text searches, prosopographic networks,
and Ur III economic balance sheets over high-performance HTTP endpoints.
"""

import os
from typing import Any, Dict, List, Literal, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from src.api.service import NisabaDataService
from src.chronos.network import ProsopographicNetwork
from src.compiler.parser import ATFParser


# Pydantic Schemas
class HealthResponse(BaseModel):
    status: str
    version: str
    service: str


class CorpusStatsResponse(BaseModel):
    total_tablets: int
    total_lines: int
    total_signs: int
    total_kmers: int
    identified_scribes: int
    audited_transactions: int
    candidate_joins: int
    engine_status: str


class TabletItem(BaseModel):
    id_text: str
    designation: Optional[str] = None
    language: Optional[str] = None
    period: Optional[str] = None
    provenance: Optional[str] = None
    line_count: Optional[int] = None
    has_date: Optional[bool] = None


class TabletListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[TabletItem]


class SearchResultItem(BaseModel):
    id_text: str
    id_line: str
    line_number: Optional[int] = None
    surface: Optional[str] = None
    raw_text: str
    normalized_text: str


# FastAPI Application
app = FastAPI(
    title="Nisaba Cuneiform Analytical API",
    description="High-throughput computational engine and REST microservice for Sumerian epigraphy, prosopography, and Ur III accounting.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for cross-origin frontend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = NisabaDataService()


@app.get("/", tags=["System"])
def root():
    """API Root endpoint providing documentation links and status."""
    return {
        "engine": "Nisaba",
        "description": "Computational Engine & Epigraphic REST API for Sumerian Cuneiform",
        "version": "1.0.0",
        "documentation": "/docs",
        "alternative_docs": "/redoc",
        "status": "ONLINE",
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    """Health check endpoint."""
    return HealthResponse(
        status="OK",
        version="1.0.0",
        service="Nisaba Analytical Microservice",
    )


@app.get("/api/stats", response_model=CorpusStatsResponse, tags=["Analytics"])
def get_corpus_stats():
    """Returns macro-aggregations across the compiled CDLI tablet database."""
    stats = service.get_stats()
    return CorpusStatsResponse(**stats)


@app.get("/api/tablets", response_model=TabletListResponse, tags=["Corpus"])
def list_tablets(
    limit: int = Query(50, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset index"),
    period: Optional[str] = Query(None, description="Filter by historical period"),
    provenance: Optional[str] = Query(None, description="Filter by city/provenance"),
    has_date: Optional[bool] = Query(None, description="Filter tablets by date presence"),
    search: Optional[str] = Query(None, description="Filter by ID (P-number) or designation"),
):
    """Lists cuneiform tablets with pagination, period filtering, and provenance attributes."""
    data = service.list_tablets(
        limit=limit,
        offset=offset,
        period=period,
        provenance=provenance,
        has_date=has_date,
        search=search,
    )
    return TabletListResponse(**data)


@app.get("/api/tablets/{id_text}", tags=["Corpus"])
def get_tablet_detail(id_text: str):
    """Retrieves full tablet details including transliteration, author attribution, dates, and CDLI photo links."""
    tablet = service.get_tablet_detail(id_text.strip().upper())
    if not tablet:
        raise HTTPException(status_code=404, detail=f"Tablet '{id_text}' not found in database.")
    return tablet


@app.get("/api/search", response_model=List[SearchResultItem], tags=["Search"])
def search_corpus(
    q: str = Query(..., min_length=2, description="Search query string"),
    mode: Literal["text", "kmer"] = Query("text", description="Search mode: text (substring) or kmer (exact 4-mer)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results to return"),
):
    """Searches for sign sequences, words, or 4-mers across all lines."""
    results = service.search_corpus(q=q, mode=mode, limit=limit)
    return results


@app.get("/api/ledger/officials", tags=["Ur III Ledger"])
def list_officials(limit: int = Query(50, ge=1, le=200, description="Number of officials to return")):
    """Returns audited officer balance sheets with credit, debit, and net inventory counts."""
    return service.list_officials(limit=limit)


@app.get("/api/ledger/transactions", tags=["Ur III Ledger"])
def list_transactions(
    officer: Optional[str] = Query(None, description="Filter by source or recipient officer"),
    commodity: Optional[str] = Query(None, description="Filter by commodity (e.g. udu, masz2, gu4)"),
    limit: int = Query(100, ge=1, le=500, description="Max transactions to return"),
):
    """Returns extracted economic transaction records."""
    return service.list_transactions(officer=officer, commodity=commodity, limit=limit)


_cached_network: Optional[ProsopographicNetwork] = None


def _get_or_build_network() -> ProsopographicNetwork:
    global _cached_network
    if _cached_network is None:
        sample_file = "data/raw/sample_cdli.atf"
        parser = ATFParser()
        tablets = parser.parse_file(sample_file)
        net = ProsopographicNetwork()
        net.build_network(tablets, min_co_occurrences=1)
        _cached_network = net
    return _cached_network


@app.get("/api/graph/prosopography", tags=["Prosopography"])
def get_prosopography_graph(
    format: Literal["cytoscape", "d3"] = Query("cytoscape", description="Graph export format"),
    min_weight: int = Query(1, ge=1, description="Minimum co-occurrence weight for edges"),
    max_nodes: int = Query(100, ge=10, le=500, description="Maximum top nodes to return"),
):
    """
    Returns the prosopographic co-occurrence network in Cytoscape.js or D3 format,
    including centrality scores and community IDs.
    """
    net = _get_or_build_network()
    if format == "d3":
        return net.to_d3_json(min_weight=min_weight, max_nodes=max_nodes)
    return net.to_cytoscape_json(min_weight=min_weight, max_nodes=max_nodes)


@app.get("/api/graph/view", response_class=HTMLResponse, tags=["Prosopography"])
def view_graph_html():
    """Renders and serves the interactive Cytoscape.js prosopography network visualizer."""
    from src.browser.network_renderer import NetworkGraphRenderer
    net = _get_or_build_network()
    renderer = NetworkGraphRenderer()
    html_path = "data/processed/prosopography_graph.html"
    renderer.render_network_html(net, output_filepath=html_path)
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()
