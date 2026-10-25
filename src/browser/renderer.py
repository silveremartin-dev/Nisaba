"""
Interactive Tablet Visual Browser for Nisaba.
Generates an advanced, responsive HTML client capable of dynamic navigation across the
entire 135,253-tablet CDLI world corpus, with embedded offline fallback support.
All UI text, tooltips, and diagnostics are strictly in English.
Features cross-linking across officials, commodities, scribes, dates, and join fragments.
"""

import html
import json
import os
import re
from typing import Dict, List, Optional

from src.compiler.parser import TabletRecord
from src.linter.engine import LinterReport
from src.chronos.solver import ChronosEstimate
from src.joins.matcher import JoinCandidate
from src.ledger.extractor import TransactionRecord


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nisaba — Sumerian Cuneiform Epigraphic Explorer</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Noto+Sans:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #090d16;
            --bg-secondary: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-cyan: #38bdf8;
            --accent-gold: #fbbf24;
            --accent-green: #4ade80;
            --accent-red: #f87171;
            --accent-purple: #c084fc;
            --border: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg-primary); color: var(--text-main); display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

        /* Top Navigation Bar */
        #topbar { background: #0b1120; border-bottom: 1px solid var(--border); height: 56px; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; z-index: 100; }
        .logo-group { display: flex; align-items: center; gap: 12px; }
        .logo-title { font-size: 1.15rem; font-weight: 700; color: var(--accent-gold); letter-spacing: 0.5px; }
        .corpus-badge { background: rgba(56, 189, 248, 0.12); color: var(--accent-cyan); border: 1px solid rgba(56, 189, 248, 0.3); padding: 3px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
        
        .nav-links { display: flex; align-items: center; gap: 8px; }
        .nav-btn { background: var(--bg-card); color: var(--text-main); border: 1px solid var(--border); padding: 6px 14px; border-radius: 6px; font-size: 0.8rem; font-weight: 500; cursor: pointer; text-decoration: none; display: flex; align-items: center; gap: 6px; transition: all 0.15s; }
        .nav-btn:hover { background: var(--bg-card-hover); border-color: var(--accent-cyan); color: #fff; }
        .nav-btn.active { background: rgba(56, 189, 248, 0.2); border-color: var(--accent-cyan); color: var(--accent-cyan); font-weight: 700; }
        .nav-btn.primary { background: #0284c7; border-color: #38bdf8; color: #fff; }
        .nav-btn.primary:hover { background: #0369a1; }

        /* Layout Container */
        #app-layout { display: flex; flex: 1; overflow: hidden; }

        /* Sidebar */
        #sidebar { width: 380px; background: var(--bg-secondary); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .sidebar-search { padding: 14px; border-bottom: 1px solid var(--border); }
        .search-input-wrapper { position: relative; }
        .search-input { width: 100%; padding: 9px 12px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; color: #fff; font-size: 0.85rem; outline: none; }
        .search-input:focus { border-color: var(--accent-cyan); }

        .filter-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-top: 10px; }
        .filter-chip { text-align: center; font-size: 0.72rem; padding: 5px 3px; border-radius: 4px; background: var(--bg-card); border: 1px solid var(--border); color: var(--text-muted); cursor: pointer; user-select: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .filter-chip:hover { border-color: var(--accent-cyan); color: #fff; }
        .filter-chip.active { background: rgba(56, 189, 248, 0.18); border-color: var(--accent-cyan); color: var(--accent-cyan); font-weight: 700; }

        .pagination-bar { padding: 8px 14px; background: #0b1120; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: var(--text-muted); }
        .page-btn { background: var(--bg-card); border: 1px solid var(--border); color: #fff; padding: 3px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75rem; font-weight: 600; }
        .page-btn:hover { background: var(--bg-card-hover); border-color: var(--accent-cyan); }
        .page-btn:disabled { opacity: 0.4; cursor: not-allowed; }

        .tablet-list { flex: 1; overflow-y: auto; list-style: none; }
        .tablet-card { padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,0.05); cursor: pointer; transition: background 0.15s; }
        .tablet-card:hover, .tablet-card.active { background: var(--bg-card); }
        .card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
        .card-id { font-weight: 700; color: var(--accent-cyan); font-size: 0.92rem; }
        .card-badge { font-size: 0.68rem; font-weight: 600; padding: 2px 6px; border-radius: 4px; }
        .badge-date { background: rgba(251, 191, 36, 0.15); color: var(--accent-gold); border: 1px solid rgba(251, 191, 36, 0.3); }
        .badge-undated { background: rgba(148, 163, 184, 0.12); color: var(--text-muted); }
        .card-desc { font-size: 0.78rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        /* Workspace */
        #workspace { flex: 1; display: flex; flex-direction: column; overflow-y: auto; background: var(--bg-primary); }
        
        .dossier-header { padding: 18px 28px; background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
        .dossier-title h2 { font-size: 1.4rem; color: #fff; display: flex; align-items: center; gap: 10px; }
        .dossier-meta { font-size: 0.82rem; color: var(--text-muted); margin-top: 8px; display: flex; flex-wrap: wrap; gap: 16px; }
        .dossier-meta span strong { color: #f1f5f9; }
        
        .dossier-grid { display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 20px; padding: 24px; }
        @media (max-width: 1200px) { .dossier-grid { grid-template-columns: 1fr; } }

        .panel { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 18px; margin-bottom: 20px; }
        .panel-header { font-size: 0.95rem; font-weight: 600; margin-bottom: 14px; color: var(--accent-cyan); border-bottom: 1px solid var(--border); padding-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }

        /* Transliteration */
        .surface-header { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: var(--accent-gold); margin: 12px 0 6px 0; font-weight: 700; }
        .line-row { display: flex; gap: 12px; font-family: "JetBrains Mono", Consolas, "Courier New", "Noto Sans", monospace; font-size: 0.88rem; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }
        .line-num { color: var(--text-muted); width: 36px; text-align: right; user-select: none; font-size: 0.8rem; }
        .line-text { color: #f1f5f9; flex: 1; word-break: break-all; font-family: inherit; letter-spacing: 0.2px; }
        
        .tok-num { color: var(--accent-gold); font-weight: bold; }
        .tok-official { color: var(--accent-cyan); cursor: pointer; text-decoration: underline dotted; }
        .tok-official:hover { color: #7dd3fc; background: rgba(56,189,248,0.15); }
        .tok-commodity { color: var(--accent-green); cursor: pointer; text-decoration: underline dotted; }
        .tok-commodity:hover { color: #86efac; background: rgba(74,222,128,0.15); }
        .tok-damage { color: var(--accent-red); opacity: 0.9; }
        .tok-verb { color: #cbd5e1; font-weight: 600; }

        /* Photo Viewer */
        .photo-box { text-align: center; }
        .photo-img { max-width: 100%; max-height: 420px; border-radius: 6px; border: 1px solid var(--border); background: #000; object-fit: contain; }
        .photo-placeholder { padding: 36px 20px; background: rgba(255,255,255,0.02); border: 1px dashed var(--border); border-radius: 6px; color: var(--text-muted); text-align: center; }

        /* Intelligence Cards */
        .intel-card { padding: 12px; border-radius: 6px; margin-bottom: 12px; font-size: 0.85rem; border: 1px solid transparent; }
        .intel-chronos { background: rgba(56, 189, 248, 0.08); border-color: rgba(56, 189, 248, 0.25); }
        .intel-scribe { background: rgba(192, 132, 252, 0.08); border-color: rgba(192, 132, 252, 0.25); }
        .intel-join { background: rgba(74, 222, 128, 0.08); border-color: rgba(74, 222, 128, 0.25); }
        .intel-metrology { background: rgba(251, 191, 36, 0.08); border-color: rgba(251, 191, 36, 0.25); }
        .intel-title { font-weight: 700; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }
        
        /* Tables */
        .data-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin-top: 8px; }
        .data-table th { text-align: left; padding: 6px 8px; background: rgba(255,255,255,0.04); color: var(--text-muted); border-bottom: 1px solid var(--border); }
        .data-table td { padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.04); }
        .click-link { color: var(--accent-cyan); cursor: pointer; text-decoration: underline; font-weight: 500; }
        .click-link:hover { color: #7dd3fc; }

        /* Offline Banner */
        #offline-alert { display: none; background: #854d0e; color: #fef08a; padding: 8px 16px; font-size: 0.8rem; text-align: center; }

        /* Modals */
        .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center; }
        .modal-box { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; width: 90%; max-width: 800px; max-height: 85vh; display: flex; flex-direction: column; overflow: hidden; }
        .modal-header { padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .modal-header h3 { color: var(--accent-gold); font-size: 1.15rem; }
        .modal-close { background: none; border: none; color: var(--text-muted); font-size: 1.4rem; cursor: pointer; }
        .modal-body { padding: 20px; overflow-y: auto; font-size: 0.88rem; line-height: 1.6; color: #e2e8f0; }
        .modal-body h4 { color: var(--accent-cyan); margin: 16px 0 6px 0; }
        .modal-body ul { margin-left: 20px; margin-bottom: 12px; }
    </style>
</head>
<body>

    <div id="offline-alert">
        ⚠️ Standalone mode: Local server not reachable. Showing cached showcase tablets. Launch <strong>start.bat</strong> to unlock dynamic full-corpus exploration.
    </div>

    <div id="topbar">
        <div class="logo-group">
            <span class="logo-title">📜 NISABA</span>
            <span class="corpus-badge" id="corpusBadge">Connecting to 135,253 Tablets...</span>
        </div>
        <div class="nav-links">
            <button class="nav-btn active" id="btnNavDossier" onclick="switchView('dossier')">🏺 Tablet Dossier</button>
            <button class="nav-btn" id="btnNavGraph" onclick="switchView('graph')">🕸️ Prosopography Graph</button>
            <button class="nav-btn" onclick="openLedgerModal()">📊 Ur III Ledger</button>
            <button class="nav-btn" onclick="openDocs()">⚡ SQL / REST API</button>
            <button class="nav-btn primary" onclick="openManualModal()">📖 User Manual</button>
        </div>
    </div>

    <div id="app-layout">
        <!-- Sidebar -->
        <div id="sidebar">
            <div class="sidebar-search">
                <div class="search-input-wrapper" style="position:relative; display:flex; align-items:center;">
                    <input type="text" id="searchInput" class="search-input" placeholder="Search P-number, official, word..." oninput="handleSearch()">
                    <button id="btnClearSearch" onclick="clearSearch()" style="position:absolute; right:8px; background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:0.9rem; display:none;" title="Clear search">✕</button>
                </div>
                <div class="filter-row">
                    <div class="filter-chip active" id="chipShowcase" onclick="setCategory('showcase')">⭐ Showcase</div>
                    <div class="filter-chip" id="chipAll" onclick="setCategory('all')">All (135k)</div>
                    <div class="filter-chip" id="chipScribes" onclick="setCategory('scribes')">✍️ Scribes</div>
                    <div class="filter-chip" id="chipDates" onclick="setCategory('dates')">⏳ Chronos</div>
                    <div class="filter-chip" id="chipTx" onclick="setCategory('transactions')">📊 Ledger</div>
                    <div class="filter-chip" id="chipJoins" onclick="setCategory('joins')">🧩 Joins</div>
                </div>
            </div>

            <div class="pagination-bar">
                <button class="page-btn" id="btnPrev" onclick="changePage(-1)">← Prev</button>
                <span id="pageIndicator">Loading...</span>
                <button class="page-btn" id="btnNext" onclick="changePage(1)">Next →</button>
            </div>

            <ul class="tablet-list" id="tabletList">
                <li style="padding: 20px; text-align: center; color: var(--text-muted); font-size: 0.85rem;">Loading tablets...</li>
            </ul>
        </div>

        <!-- Main Workspace -->
        <div id="workspace">
            <!-- View 1: Tablet Dossier -->
            <div id="viewDossierContainer" style="display:flex; flex-direction:column; flex:1; overflow-y:auto; height:100%;">
                <div class="dossier-header">
                    <div class="dossier-title">
                        <h2 id="viewId">Select a Tablet</h2>
                        <div class="dossier-meta">
                            <span>Designation: <strong id="viewDesignation">—</strong></span>
                            <span>Period: <strong id="viewPeriod">—</strong></span>
                            <span>Provenance: <strong id="viewProvenance">—</strong></span>
                            <span>Lines: <strong id="viewLines">—</strong></span>
                            <span>Source: <a id="viewSourceLink" href="#" target="_blank" style="color:var(--accent-cyan); font-weight:600; text-decoration:underline;">—</a></span>
                        </div>
                    </div>
                </div>

                <div class="dossier-grid">
                <!-- Left Column: Transliteration & Metrology & Ledger -->
                <div>
                    <!-- Transliteration Panel -->
                    <div class="panel">
                        <div class="panel-header">
                            <span>Sumerian Cuneiform Transliteration</span>
                            <div style="display:flex; align-items:center; gap:8px;">
                                <button class="page-btn" id="btnTranslitMode" onclick="toggleTranslitMode()">🔤 Unicode (š, ṣ, ṭ) ⇄ ASCII</button>
                                <span style="font-size:0.75rem; color:var(--text-muted);" id="translitBadge">C-ATF</span>
                            </div>
                        </div>
                        <div id="transliterationContent">
                            <p style="color:var(--text-muted); font-size:0.85rem;">Select a tablet from the list to view its transliteration.</p>
                        </div>
                    </div>

                    <!-- Metrology & Measures Panel -->
                    <div class="panel" id="metrologyPanel" style="display:none;">
                        <div class="panel-header">
                            <span>⚖️ Metrological Measures & Metric Equivalents</span>
                            <span style="font-size:0.75rem; color:var(--accent-gold);" id="metroBadge">Converted</span>
                        </div>
                        <div style="overflow-x:auto;">
                            <table class="data-table" id="metroTable">
                                <thead>
                                    <tr>
                                        <th>Line</th>
                                        <th>Measurement Type</th>
                                        <th>Ancient Units</th>
                                        <th>Metric Equivalent</th>
                                    </tr>
                                </thead>
                                <tbody id="metroBody"></tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Transactions Panel -->
                    <div class="panel" id="txPanel" style="display:none;">
                        <div class="panel-header">
                            <span>Ur III Economic Transactions</span>
                            <span style="font-size:0.75rem; color:var(--accent-gold);" id="txCountBadge">0 transactions</span>
                        </div>
                        <div style="overflow-x:auto;">
                            <table class="data-table" id="txTable">
                                <thead>
                                    <tr>
                                        <th>Qty</th>
                                        <th>Commodity</th>
                                        <th>Source (ki...-ta)</th>
                                        <th>Recipient (i3-dab5)</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody id="txBody"></tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Right Column: Photography & Epigraphic Intelligence -->
                <div>
                    <!-- Museum Photograph -->
                    <div class="panel">
                        <div class="panel-header">
                            <span>Museum Photograph</span>
                            <span id="photoBadge" style="font-size:0.72rem; color:var(--accent-cyan);">Archive Record</span>
                        </div>
                        <div class="photo-box" id="photoBox">
                            <div class="photo-placeholder">No photograph loaded</div>
                        </div>
                    </div>

                    <!-- Intelligence Engines -->
                    <div class="panel">
                        <div class="panel-header">Epigraphic Intelligence Engines</div>
                        
                        <!-- Chronos Date -->
                        <div class="intel-card intel-chronos" id="chronosCard">
                            <div class="intel-title">
                                <span>⏳ Chronos Macro-Chronology</span>
                                <span id="chronosStatusBadge" class="card-badge badge-date">Resolving...</span>
                            </div>
                            <div id="chronosDetails" style="margin-top:6px; color:#cbd5e1;">—</div>
                        </div>

                        <!-- Scribe Attribution -->
                        <div class="intel-card intel-scribe" id="scribeCard">
                            <div class="intel-title">
                                <span>✍️ Ancient Scribe & Cylinder Seal</span>
                                <span id="scribeConfidence" class="card-badge" style="background:rgba(192,132,252,0.2); color:var(--accent-purple);">—</span>
                            </div>
                            <div id="scribeDetails" style="margin-top:6px; color:#cbd5e1;">—</div>
                        </div>

                        <!-- Candidate Joins -->
                        <div class="intel-card intel-join" id="joinCard">
                            <div class="intel-title">
                                <span>🧩 Fragment Joins & Duplicates</span>
                                <span id="joinCountBadge" class="card-badge" style="background:rgba(74,222,128,0.2); color:var(--accent-green);">—</span>
                            </div>
                            <div id="joinDetails" style="margin-top:6px; color:#cbd5e1;">—</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- In-Page Prosopography Graph View (No new tabs) -->
            <div id="viewGraphContainer" style="display:none; flex:1; height:100%; position:relative;">
                <div style="position:absolute; top:12px; right:20px; z-index:100; display:flex; gap:8px;">
                    <button class="nav-btn" onclick="switchView('dossier')">← Back to Tablet Dossier</button>
                    <a id="btnExternalGraph" href="/api/graph/view" target="_blank" class="nav-btn" title="Open graph in separate window if needed">Open in New Tab ↗</a>
                </div>
                <iframe id="graphFrame" src="" style="width:100%; height:100%; border:none; background:#0b0f19;"></iframe>
            </div>
        </div>
    </div>

    <!-- User Manual Modal -->
    <div class="modal-overlay" id="manualModal">
        <div class="modal-box">
            <div class="modal-header">
                <h3>📖 Nisaba — Epigraphic User Manual & Quick Guide</h3>
                <button class="modal-close" onclick="closeModal('manualModal')">&times;</button>
            </div>
            <div class="modal-body">
                <h4>What is Nisaba?</h4>
                <p>Nisaba is a high-throughput epigraphic computational suite for ancient Sumerian cuneiform. It turns raw archival text into certified columnar databases, dates broken tablets, attributes scribes, audits double-entry accounting ledgers, and detects cross-museum virtual joins.</p>

                <h4>1. Cross-Linking & Navigation</h4>
                <p>Everything in the tablet dossier is interconnected: click any official name in the transliteration or transaction table to filter all tablets involving that official. Click a scribe name or Chronos date to find related chancery tablets. Click a candidate join fragment ID to open that tablet immediately.</p>

                <h4>2. Category Filter Chips</h4>
                <p>Use the chips in the sidebar to jump between: ⭐ <strong>Showcase</strong> (tablets with photos and verified joins), ✍️ <strong>Scribes</strong> (35,000+ tablets with attributed scribes), ⏳ <strong>Chronos</strong> (dated tablets), 📊 <strong>Ledger</strong> (accounting transactions), and 🧩 <strong>Joins</strong> (cross-museum fragment joins).</p>

                <h4>3. Metrological Measures & Metric Equivalents</h4>
                <p>Nisaba parses ancient Sumerian capacity (gur, barig, ban2, sila3) and weight units (gu2, ma-na, gin2), providing modern metric equivalents (liters of grain/beer, kilograms of wool/metals, discrete livestock counts).</p>

                <h4>4. Prosopographic Interaction Graph</h4>
                <p>Click the <strong>🕸️ Prosopography Graph</strong> link in the top bar to inspect the interactive social and bureaucratic network of hundreds of Sumerian officials, with direct clickable links back to their tablets.</p>
            </div>
        </div>
    </div>

    <!-- Ur III Ledger Balances Modal -->
    <div class="modal-overlay" id="ledgerModal">
        <div class="modal-box">
            <div class="modal-header">
                <h3>📊 Ur III Administrative Ledger — Officer Balances</h3>
                <button class="modal-close" onclick="closeModal('ledgerModal')">&times;</button>
            </div>
            <div class="modal-body">
                <p style="color:var(--text-muted); margin-bottom: 12px;">Top active officials across the central livestock and grain clearing bureaus:</p>
                <div style="overflow-x:auto;">
                    <table class="data-table" style="font-size:0.85rem;">
                        <thead>
                            <tr>
                                <th>Officer Name</th>
                                <th>Commodity</th>
                                <th>Total Received</th>
                                <th>Total Expended</th>
                                <th>Net Inventory Balance</th>
                            </tr>
                        </thead>
                        <tbody id="ledgerModalBody">
                            <tr><td colspan="5" style="text-align:center; padding:15px; color:var(--text-muted);">Loading balances from DuckDB...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Client-Side Application Logic & Fallback Data -->
    <script>
        const FALLBACK_TABLETS = {{ fallback_json | safe }};
        const API_BASE = (window.location.protocol === 'http:' || window.location.protocol === 'https:') ? '' : 'http://127.0.0.1:8000';
        let isOnline = false;
        let currentPage = 1;
        const pageSize = 50;
        let currentCategory = 'showcase';
        let currentSearch = '';
        let currentSelectedId = null;
        let currentLoadedTablet = null;
        let useAssyriologicalUnicode = false;

        function switchView(view) {
            const dossier = document.getElementById('viewDossierContainer');
            const graph = document.getElementById('viewGraphContainer');
            const btnDossier = document.getElementById('btnNavDossier');
            const btnGraph = document.getElementById('btnNavGraph');

            if (view === 'graph') {
                dossier.style.display = 'none';
                graph.style.display = 'block';
                const frame = document.getElementById('graphFrame');
                const targetSrc = (window.location.protocol === 'file:') ? 'prosopography_graph.html' : `${API_BASE}/api/graph/view`;
                if (!frame.src || frame.src === 'about:blank' || !frame.src.endsWith(targetSrc)) {
                    frame.src = targetSrc;
                }
                btnDossier.classList.remove('active');
                btnGraph.classList.add('active');
            } else {
                dossier.style.display = 'flex';
                graph.style.display = 'none';
                btnDossier.classList.add('active');
                btnGraph.classList.remove('active');
            }
        }

        window.switchView = switchView;
        window.selectTabletFromGraph = function(tabletId) {
            switchView('dossier');
            selectTablet(tabletId);
        };

        function openDocs() {
            window.open(`${API_BASE}/docs`, '_blank');
        }

        function toAssyriologicalUnicode(text) {
            if (!text) return '';
            let t = text;
            t = t.replace(/sz/g, 'š').replace(/SZ/g, 'Š');
            t = t.replace(/s,/g, 'ṣ').replace(/S,/g, 'Ṣ');
            t = t.replace(/t,/g, 'ṭ').replace(/T,/g, 'Ṭ');
            t = t.replace(/g~/g, 'ĝ').replace(/G~/g, 'Ĝ');
            t = t.replace(/h,/g, 'ḫ').replace(/H,/g, 'Ḫ');
            const subs = {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉','x':'ₓ'};
            t = t.replace(/([a-zA-ZšŠṣṢṭṬĝĜḫḪ])([0-9x])\b/g, (m, c, d) => c + (subs[d] || d));
            return t;
        }

        function toggleTranslitMode() {
            useAssyriologicalUnicode = !useAssyriologicalUnicode;
            const btn = document.getElementById('btnTranslitMode');
            if (btn) {
                btn.innerText = useAssyriologicalUnicode ? '🔤 Unicode Active (š, ṣ, ṭ)' : '🔤 Convert to Unicode';
                btn.style.borderColor = useAssyriologicalUnicode ? 'var(--accent-cyan)' : 'var(--border)';
                btn.style.color = useAssyriologicalUnicode ? 'var(--accent-cyan)' : '#fff';
            }
            if (currentLoadedTablet) {
                renderTransliteration(currentLoadedTablet);
            }
        }

        async function init() {
            // Check hash in URL (e.g. #P100004)
            if (window.location.hash) {
                const target = window.location.hash.replace('#', '').trim().toUpperCase();
                if (target.startsWith('P')) currentSelectedId = target;
            }

            // Check URL search parameter
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('search')) {
                currentSearch = urlParams.get('search');
                document.getElementById('searchInput').value = currentSearch;
                currentCategory = 'all';
                updateCategoryChips();
            }

            try {
                const res = await fetch(`${API_BASE}/api/stats`, { signal: AbortSignal.timeout(2000) });
                if (res.ok) {
                    const stats = await res.json();
                    isOnline = true;
                    const totalTabs = stats.total_tablets || 135253;
                    document.getElementById('corpusBadge').innerText = `Online: ${totalTabs.toLocaleString()} Tablets`;
                }
            } catch (e) {
                isOnline = false;
                document.getElementById('offline-alert').style.display = 'block';
                document.getElementById('corpusBadge').innerText = `Offline: ${FALLBACK_TABLETS.length} Sample Tablets`;
            }

            loadPage(1);
        }

        async function loadPage(page) {
            currentPage = page;
            const offset = (page - 1) * pageSize;

            if (isOnline) {
                let url = `${API_BASE}/api/tablets?limit=${pageSize}&offset=${offset}&category=${currentCategory}`;
                if (currentSearch.trim()) url += `&search=${encodeURIComponent(currentSearch.trim())}`;

                try {
                    const res = await fetch(url);
                    const data = await res.json();
                    renderTabletList(data.items, data.total);
                    return;
                } catch (e) {
                    console.warn('API error, falling back:', e);
                }
            }

            // Fallback rendering
            let filtered = FALLBACK_TABLETS;
            if (currentCategory === 'scribes') {
                filtered = filtered.filter(t => t.attribution && t.attribution.identified_scribe && t.attribution.identified_scribe !== 'Unknown');
            } else if (currentCategory === 'dates') {
                filtered = filtered.filter(t => t.has_date || (t.chronos_estimate && t.chronos_estimate.status && t.chronos_estimate.status !== 'UNDETERMINED'));
            } else if (currentCategory === 'transactions') {
                filtered = filtered.filter(t => t.transactions && t.transactions.length > 0);
            } else if (currentCategory === 'joins') {
                filtered = filtered.filter(t => t.candidate_joins && t.candidate_joins.length > 0);
            }

            if (currentSearch.trim()) {
                const q = currentSearch.toLowerCase();
                filtered = filtered.filter(t => {
                    const matchId = t.id_text && t.id_text.toLowerCase().includes(q);
                    const matchDesig = t.designation && t.designation.toLowerCase().includes(q);
                    const matchScribe = t.attribution && t.attribution.identified_scribe && t.attribution.identified_scribe.toLowerCase().includes(q);
                    const matchTx = t.transactions && t.transactions.some(tx => 
                        (tx.commodity && tx.commodity.toLowerCase().includes(q)) ||
                        (tx.source_party && tx.source_party.toLowerCase().includes(q)) ||
                        (tx.receiving_party && tx.receiving_party.toLowerCase().includes(q))
                    );
                    const matchLines = t.lines && t.lines.some(l => 
                        (l.raw_text && l.raw_text.toLowerCase().includes(q)) ||
                        (l.normalized_text && l.normalized_text.toLowerCase().includes(q))
                    );
                    return matchId || matchDesig || matchScribe || matchTx || matchLines;
                });
            }

            const slice = filtered.slice(offset, offset + pageSize);
            renderTabletList(slice, filtered.length);
        }

        function renderTabletList(items, totalCount) {
            const listEl = document.getElementById('tabletList');
            listEl.innerHTML = '';

            const maxPage = Math.max(1, Math.ceil(totalCount / pageSize));
            document.getElementById('pageIndicator').innerText = `Page ${currentPage} / ${maxPage.toLocaleString()} (${totalCount.toLocaleString()} texts)`;
            document.getElementById('btnPrev').disabled = currentPage <= 1;
            document.getElementById('btnNext').disabled = currentPage >= maxPage;

            if (!items || items.length === 0) {
                listEl.innerHTML = '<li style="padding: 20px; text-align: center; color: var(--text-muted); font-size: 0.85rem;">No tablets found.</li>';
                return;
            }

            items.forEach((item, idx) => {
                const li = document.createElement('li');
                li.className = `tablet-card ${idx === 0 && !currentSelectedId ? 'active' : ''} ${item.id_text === currentSelectedId ? 'active' : ''}`;
                li.id = `card-${item.id_text}`;
                li.onclick = () => selectTablet(item.id_text);

                const hasDate = item.has_date;
                const badgeClass = hasDate ? 'badge-date' : 'badge-undated';
                const badgeText = hasDate ? 'Dated' : 'Undated';

                li.innerHTML = `
                    <div class="card-top">
                        <span class="card-id">${item.id_text}</span>
                        <span class="card-badge ${badgeClass}">${badgeText}</span>
                    </div>
                    <div class="card-desc">${item.designation || 'Inscription'} • ${item.line_count || 0} lines</div>
                `;
                listEl.appendChild(li);
            });

            if (!currentSelectedId && items.length > 0) {
                selectTablet(items[0].id_text);
            } else if (currentSelectedId) {
                selectTablet(currentSelectedId);
            }
        }

        async function selectTablet(idText) {
            currentSelectedId = idText;
            window.location.hash = idText;
            document.querySelectorAll('.tablet-card').forEach(c => c.classList.remove('active'));
            const card = document.getElementById(`card-${idText}`);
            if (card) card.classList.add('active');

            if (isOnline) {
                try {
                    const res = await fetch(`${API_BASE}/api/tablets/${idText}`);
                    if (res.ok) {
                        const tablet = await res.json();
                        renderTabletDetails(tablet);
                        return;
                    }
                } catch (e) {
                    console.warn('API detail fetch failed:', e);
                }
            }

            // Fallback detail
            const item = FALLBACK_TABLETS.find(t => t.id_text === idText);
            if (item) renderTabletDetails(item);
        }

        function renderTabletDetails(tab) {
            currentLoadedTablet = tab;
            document.getElementById('viewId').innerText = tab.id_text;
            document.getElementById('viewDesignation').innerText = tab.designation || 'Unknown';
            document.getElementById('viewPeriod').innerText = tab.period || 'Ur III (ca. 2112–2004 BC)';
            document.getElementById('viewProvenance').innerText = tab.provenance || 'Southern Mesopotamia (Sumer)';
            document.getElementById('viewLines').innerText = tab.lines ? tab.lines.length : (tab.line_count || 0);

            // Source Link
            const numId = (tab.id_text || '').replace(/^P/, '');
            const cdliUrl = 'https://cdli.mpiwg-berlin.mpg.de/artifacts/' + numId;
            const srcLink = document.getElementById('viewSourceLink');
            if (srcLink) {
                srcLink.href = cdliUrl;
                srcLink.innerText = `CDLI (${tab.id_text}) ↗`;
            }

            // High-Resolution Photograph or Lineart Hand Copy Drawing (Cascading Fallback)
            renderPhoto(tab, cdliUrl);

            // Transliteration with Cross-Linking
            renderTransliteration(tab);

            // Metrology Panel
            const metroPanel = document.getElementById('metrologyPanel');
            const metroBody = document.getElementById('metroBody');
            if (tab.metrology && tab.metrology.length > 0) {
                metroPanel.style.display = 'block';
                metroBody.innerHTML = tab.metrology.map(m => `
                    <tr>
                        <td style="color:var(--text-muted);">${m.line || '—'}</td>
                        <td style="color:var(--accent-cyan); font-weight:600;">${m.type}</td>
                        <td style="color:var(--accent-gold); font-family:monospace;">${m.ancient_units}</td>
                        <td style="color:var(--accent-green); font-weight:700;">${m.metric_equivalent}</td>
                    </tr>
                `).join('');
            } else {
                metroPanel.style.display = 'none';
            }

            // Transactions Table with Cross-Linking
            const txPanel = document.getElementById('txPanel');
            const txBody = document.getElementById('txBody');
            if (tab.transactions && tab.transactions.length > 0) {
                txPanel.style.display = 'block';
                document.getElementById('txCountBadge').innerText = `${tab.transactions.length} transactions`;
                txBody.innerHTML = tab.transactions.map(tx => `
                    <tr>
                        <td style="color:var(--accent-gold); font-weight:bold;">${tx.quantity}</td>
                        <td><span class="click-link" onclick="filterBySearch('${tx.commodity}')">${tx.commodity}</span></td>
                        <td>${tx.source_party && tx.source_party !== 'Unknown' ? `<span class="click-link" onclick="filterBySearch('${tx.source_party}')">${tx.source_party}</span>` : '—'}</td>
                        <td>${tx.receiving_party && tx.receiving_party !== 'Unknown' ? `<span class="click-link" onclick="filterBySearch('${tx.receiving_party}')">${tx.receiving_party}</span>` : '—'}</td>
                        <td><span class="card-badge" style="background:rgba(56,189,248,0.15); color:var(--accent-cyan);">${tx.action_type || 'TRANSACTION'}</span></td>
                    </tr>
                `).join('');
            } else {
                txPanel.style.display = 'none';
            }

            // Chronos Card with Cross-Link
            const chronosBadge = document.getElementById('chronosStatusBadge');
            const chronosDetails = document.getElementById('chronosDetails');
            if (tab.chronos_estimate && tab.chronos_estimate.status) {
                const est = tab.chronos_estimate;
                chronosBadge.innerText = est.status;
                const yearLink = est.resolved_year ? `<span class="click-link" onclick="filterBySearch('${est.resolved_year}')">${est.resolved_year}</span>` : 'Unknown';
                chronosDetails.innerHTML = `
                    <div><strong>Resolved Year:</strong> ${yearLink}</div>
                    <div style="font-size:0.78rem; color:var(--text-muted); margin-top:3px;">Confidence: ${(est.confidence * 100).toFixed(0)}% • Historical Imperial Ur III Chronology</div>
                `;
            } else {
                chronosBadge.innerText = 'UNDETERMINED';
                chronosDetails.innerText = 'No temporal prosopographic constraints detected on this tablet.';
            }

            // Scribe Card with Cross-Link
            const scribeConf = document.getElementById('scribeConfidence');
            const scribeDetails = document.getElementById('scribeDetails');
            if (tab.attribution && tab.attribution.identified_scribe && tab.attribution.identified_scribe !== 'Unknown') {
                const a = tab.attribution;
                scribeConf.innerText = `${(a.confidence * 100).toFixed(0)}% Confidence`;
                const scribeLink = `<span class="click-link" onclick="filterBySearch('${a.identified_scribe}')">${a.identified_scribe}</span>`;
                scribeDetails.innerHTML = `
                    <div><strong>Scribe:</strong> ${scribeLink}</div>
                    <div style="font-size:0.78rem; color:var(--text-muted); margin-top:3px;">Title: ${a.title || 'dub-sar'} • Father: ${a.patronymic || '—'}</div>
                `;
            } else {
                scribeConf.innerText = 'Anonymous';
                scribeDetails.innerText = 'No cylinder seal impression or scribal colophon attested.';
            }

            // Joins Card with Direct Jump Button
            const joinBadge = document.getElementById('joinCountBadge');
            const joinDetails = document.getElementById('joinDetails');
            if (tab.candidate_joins && tab.candidate_joins.length > 0) {
                joinBadge.innerText = `${tab.candidate_joins.length} Candidates`;
                joinDetails.innerHTML = tab.candidate_joins.map(j => {
                    const otherId = (j.id_text_a === tab.id_text) ? j.id_text_b : j.id_text_a;
                    const isJumpable = otherId.startsWith('P');
                    return `
                        <div style="font-size:0.82rem; margin-top:6px; display:flex; justify-content:space-between; align-items:center;">
                            <span>• <strong>${otherId}</strong> (${(j.similarity_score * 100).toFixed(0)}% match, ${j.join_type})</span>
                            ${isJumpable ? `<button class="page-btn" onclick="selectTablet('${otherId}')">Open Tablet ↗</button>` : ''}
                        </div>
                    `;
                }).join('');
            } else {
                joinBadge.innerText = '0 Matches';
                joinDetails.innerText = 'No physical or virtual sequence matches detected.';
            }
        }

        function renderTransliteration(tab) {
            const translitBox = document.getElementById('transliterationContent');
            if (tab.lines && tab.lines.length > 0) {
                let htmlLines = '';
                let lastSurface = '';
                tab.lines.forEach(l => {
                    if (l.surface && l.surface !== lastSurface) {
                        lastSurface = l.surface;
                        htmlLines += `<div class="surface-header">@${l.surface}</div>`;
                    }
                    let lineStr = l.raw_text || l.normalized_text || '';
                    if (useAssyriologicalUnicode) {
                        lineStr = toAssyriologicalUnicode(lineStr);
                    }
                    const text = highlightLine(lineStr);
                    htmlLines += `
                        <div class="line-row">
                            <span class="line-num">${l.line_number || ''}</span>
                            <span class="line-text">${text}</span>
                        </div>
                    `;
                });
                translitBox.innerHTML = htmlLines;
            } else {
                translitBox.innerHTML = '<p style="color:var(--text-muted); font-size:0.85rem;">No transliteration lines recorded.</p>';
            }
        }

        function renderPhoto(tab, cdliUrl) {
            const photoBox = document.getElementById('photoBox');
            const sources = [];

            if (tab.photos && tab.photos.local_image_url) {
                const loc = tab.photos.local_image_url.startsWith('http') 
                    ? tab.photos.local_image_url 
                    : `${API_BASE}${tab.photos.local_image_url}`;
                sources.push({ url: loc, isDrawing: false, label: '📷 Local Museum Photo Archive' });
            }
            sources.push({ 
                url: `https://cdli.mpiwg-berlin.mpg.de/dl/photo/${tab.id_text}.jpg`, 
                isDrawing: false, 
                label: '📷 High-Resolution Museum Photograph' 
            });
            sources.push({ 
                url: `https://cdli.mpiwg-berlin.mpg.de/dl/lineart/${tab.id_text}_l.jpg`, 
                isDrawing: true, 
                label: '🖋️ CDLI Epigraphic Hand Copy (Drawing)' 
            });
            sources.push({ 
                url: `https://cdli.mpiwg-berlin.mpg.de/dl/tn_lineart/${tab.id_text}_l.jpg`, 
                isDrawing: true, 
                label: '🖋️ CDLI Epigraphic Line Art Drawing' 
            });

            let srcIdx = 0;
            function tryNext() {
                if (srcIdx >= sources.length) {
                    showPhotoPlaceholder(cdliUrl, tab.id_text);
                    return;
                }
                const current = sources[srcIdx++];
                const testImg = new Image();
                testImg.onload = function() {
                    const tagColor = current.isDrawing ? 'var(--accent-gold)' : 'var(--accent-cyan)';
                    photoBox.innerHTML = `
                        <img src="${current.url}" class="photo-img" alt="Tablet ${tab.id_text}">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                            <span style="font-size:0.75rem; color:${tagColor}; font-weight:600;">${current.label}</span>
                            <a href="${cdliUrl}" target="_blank" style="color:var(--accent-cyan); font-size:0.8rem; text-decoration:none; font-weight:600;">🔗 Source: CDLI (${tab.id_text}) ↗</a>
                        </div>
                    `;
                };
                testImg.onerror = function() {
                    tryNext();
                };
                testImg.src = current.url;
            }

            tryNext();
        }

        function showPhotoPlaceholder(cdliUrl, idText) {
            const url = cdliUrl || ('https://cdli.mpiwg-berlin.mpg.de/artifacts/' + (currentSelectedId || '').replace(/^P/, ''));
            const id = idText || currentSelectedId || 'CDLI Record';
            const box = document.getElementById('photoBox');
            box.innerHTML = `
                <div class="photo-placeholder">
                    <div style="font-size:2rem; margin-bottom:8px;">🏛️</div>
                    <div style="font-weight:700; color:#f8fafc; font-size:0.95rem;">No Photo or Drawing Cataloged</div>
                    <div style="font-size:0.8rem; color:#94a3b8; margin: 6px 0 12px 0;">This accession tablet does not currently have an open high-res photograph or hand drawing.</div>
                    <a href="${url}" target="_blank" class="nav-btn primary" style="display:inline-flex; align-items:center; gap:6px; text-decoration:none;">
                        🔗 Source: CDLI (${id}) ↗
                    </a>
                </div>
            `;
        }

        function highlightLine(raw) {
            let s = raw.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            // Damage flags
            s = s.replace(/(\[.*?\])/g, '<span class="tok-damage">$1</span>');
            s = s.replace(/([a-z0-9_\-]+[#\?!]+)/gi, '<span class="tok-damage">$1</span>');
            // Quantities
            s = s.replace(/(\b\d+\([a-z0-9\']+\))/gi, '<span class="tok-num">$1</span>');
            // Key officials (clickable)
            s = s.replace(/\b(ab-ba-sa6-ga|na-lu5|in-ta-e3-a|du11-ga|lu2-kal-la|ur-mes|ur-szu-ga-lam-ma|{d}szul-gi-a-a-mu|ensi2-ka|da-da-ga|usz-mu|kas4)\b/gi, 
                '<span class="tok-official" onclick="filterBySearch(\'$1\')">$1</span>');
            // Key commodities (clickable)
            s = s.replace(/\b(udu|masz2|gu4|sila4|sze|kasz|zi3|ku3-babbar)\b/gi, 
                '<span class="tok-commodity" onclick="filterBySearch(\'$1\')">$1</span>');
            // Key verbs
            s = s.replace(/\b(i3-dab5|ba-zi|ki|kiszib3|mu-kux\(DU\))\b/g, '<span class="tok-verb">$1</span>');
            return s;
        }

        function filterBySearch(term) {
            currentSearch = term;
            document.getElementById('searchInput').value = term;
            const clearBtn = document.getElementById('btnClearSearch');
            if (clearBtn) clearBtn.style.display = 'block';
            currentCategory = 'all';
            updateCategoryChips();
            document.getElementById('tabletList').innerHTML = '<li style="padding: 20px; text-align: center; color: var(--accent-cyan); font-size: 0.85rem;">⏳ Searching for "' + term + '"...</li>';
            loadPage(1);
        }

        let searchTimer = null;
        function handleSearch() {
            const val = document.getElementById('searchInput').value;
            const clearBtn = document.getElementById('btnClearSearch');
            if (clearBtn) clearBtn.style.display = val.trim() ? 'block' : 'none';
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                currentSearch = val;
                loadPage(1);
            }, 300);
        }

        function clearSearch() {
            currentSearch = '';
            document.getElementById('searchInput').value = '';
            const clearBtn = document.getElementById('btnClearSearch');
            if (clearBtn) clearBtn.style.display = 'none';
            loadPage(1);
        }

        function setCategory(cat) {
            currentCategory = cat;
            currentSearch = '';
            document.getElementById('searchInput').value = '';
            const clearBtn = document.getElementById('btnClearSearch');
            if (clearBtn) clearBtn.style.display = 'none';
            updateCategoryChips();
            document.getElementById('tabletList').innerHTML = '<li style="padding: 20px; text-align: center; color: var(--accent-cyan); font-size: 0.85rem;">⏳ Loading ' + cat + ' tablets...</li>';
            loadPage(1);
        }

        function updateCategoryChips() {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            if (currentCategory === 'showcase') document.getElementById('chipShowcase').classList.add('active');
            if (currentCategory === 'all') document.getElementById('chipAll').classList.add('active');
            if (currentCategory === 'scribes') document.getElementById('chipScribes').classList.add('active');
            if (currentCategory === 'dates') document.getElementById('chipDates').classList.add('active');
            if (currentCategory === 'transactions') document.getElementById('chipTx').classList.add('active');
            if (currentCategory === 'joins') document.getElementById('chipJoins').classList.add('active');
        }

        function changePage(delta) {
            loadPage(currentPage + delta);
        }

        // Modals
        function openManualModal() {
            document.getElementById('manualModal').style.display = 'flex';
        }
        async function openLedgerModal() {
            document.getElementById('ledgerModal').style.display = 'flex';
            const body = document.getElementById('ledgerModalBody');
            body.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:15px; color:var(--text-muted);">Loading balances from DuckDB...</td></tr>';
            try {
                const res = await fetch(`${API_BASE}/api/ledger/officials?limit=25`);
                if (res.ok) {
                    const items = await res.json();
                    body.innerHTML = items.map(o => `
                        <tr>
                            <td><span class="click-link" onclick="closeModal('ledgerModal'); filterBySearch('${o.officer}')">${o.officer}</span></td>
                            <td style="color:var(--accent-green);">${o.commodity}</td>
                            <td>${o.total_received.toLocaleString()}</td>
                            <td>${o.total_expended.toLocaleString()}</td>
                            <td style="color:${o.net_inventory >= 0 ? 'var(--accent-gold)' : 'var(--accent-red)'}; font-weight:bold;">${o.net_inventory.toLocaleString()}</td>
                        </tr>
                    `).join('');
                }
            } catch (e) {
                console.warn(e);
                body.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:15px; color:var(--accent-red);">Unable to fetch live ledger balances. Please ensure start.bat is running.</td></tr>';
            }
        }
        function closeModal(id) {
            document.getElementById(id).style.display = 'none';
        }
        window.onclick = (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                e.target.style.display = 'none';
            }
        };

        window.onload = init;
    </script>
</body>
</html>
"""


class TabletBrowserRenderer:
    """Renders the standalone interactive visual browser."""

    def render_corpus(
        self,
        tablets: List[TabletRecord],
        linter_report: Optional[LinterReport] = None,
        estimates: Optional[List[ChronosEstimate]] = None,
        joins: Optional[List[JoinCandidate]] = None,
        transactions: Optional[List[TransactionRecord]] = None,
        attributions: Optional[list] = None,
        output_filepath: str = "data/processed/browser.html",
    ) -> str:
        """Compiles tablet data into the interactive HTML application."""
        os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)

        from src.ledger.metrology import MetrologyEngine
        metrology_engine = MetrologyEngine()

        est_map = {e.id_text: e for e in (estimates or [])}
        attr_map = {a.id_text: a for a in (attributions or [])}
        joins_map: Dict[str, list] = {}
        if joins:
            for j in joins:
                joins_map.setdefault(j.id_text_a, []).append({
                    "id_text_a": j.id_text_a,
                    "id_text_b": j.id_text_b,
                    "join_type": j.join_type,
                    "similarity_score": j.similarity_score,
                })
                joins_map.setdefault(j.id_text_b, []).append({
                    "id_text_a": j.id_text_a,
                    "id_text_b": j.id_text_b,
                    "join_type": j.join_type,
                    "similarity_score": j.similarity_score,
                })

        tx_map: Dict[str, list] = {}
        if transactions:
            for tx in transactions:
                tx_map.setdefault(tx.id_text, []).append({
                    "quantity": tx.quantity,
                    "commodity": tx.commodity,
                    "source_party": tx.source_party,
                    "receiving_party": tx.receiving_party,
                    "action_type": tx.action_type,
                })

        sample_items = []
        for tab in tablets[:50]:
            p_clean = tab.id_text.strip().upper()
            local_img = os.path.exists(os.path.join("assets", "real_tablets", f"{p_clean}.jpg"))
            
            est = est_map.get(tab.id_text)
            attr = attr_map.get(tab.id_text)
            lines_dicts = [
                {
                    "surface": l.surface,
                    "line_number": l.line_number,
                    "raw_text": l.raw_text,
                    "normalized_text": l.normalized_text,
                }
                for l in tab.lines
            ]

            sample_items.append({
                "id_text": tab.id_text,
                "designation": tab.designation,
                "period": tab.period or "Ur III (ca. 2112–2004 BC)",
                "provenance": tab.provenance or "Puzrish-Dagan (Drehem) — Royal Livestock Bureau",
                "line_count": len(tab.lines),
                "has_date": tab.has_date,
                "lines": lines_dicts,
                "photos": {
                    "has_local_image": local_img,
                    "local_image_url": f"/assets/real_tablets/{p_clean}.jpg" if local_img else None,
                    "cdli_image_url": f"https://cdli.mpiwg-berlin.mpg.de/dl/photo/{p_clean}.jpg",
                },
                "metrology": metrology_engine.parse_tablet_metrology(lines_dicts),
                "chronos_estimate": {
                    "resolved_year": est.resolved_year if est else None,
                    "status": est.status if est else ("CERTIFIED_DATED" if tab.has_date else "UNDETERMINED"),
                    "confidence": est.confidence if est else (1.0 if tab.has_date else 0.0),
                } if est else None,
                "attribution": {
                    "identified_scribe": attr.identified_scribe if attr else "Unknown",
                    "patronymic": attr.patronymic if attr else "Unknown",
                    "title": attr.title if attr else "dub-sar",
                    "confidence": attr.confidence if attr else 0.0,
                } if attr else None,
                "transactions": tx_map.get(tab.id_text, []),
                "candidate_joins": joins_map.get(tab.id_text, []),
            })

        fallback_json = json.dumps(sample_items)
        html_content = HTML_TEMPLATE.replace("{{ fallback_json | safe }}", fallback_json)

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_filepath
