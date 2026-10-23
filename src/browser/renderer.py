"""
Interactive Tablet Visual Browser for Nisaba.
Generates a standalone, rich HTML explorer displaying tablet imagery, transliteration,
color-coded linguistic entities, linter diagnostics, Chronos dates, and virtual join matches.
"""

import html
import json
import os
import re
from typing import Dict, List, Optional
from jinja2 import Template

from src.compiler.parser import TabletRecord
from src.linter.engine import LinterReport
from src.chronos.solver import ChronosEstimate
from src.joins.matcher import JoinCandidate
from src.ledger.extractor import TransactionRecord


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nisaba — Tablet Visual Explorer</title>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-cyan: #38bdf8;
            --accent-gold: #fbbf24;
            --accent-green: #4ade80;
            --accent-red: #f87171;
            --border: #475569;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg-primary); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar */
        #sidebar { width: 340px; background: var(--bg-secondary); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .sidebar-header { padding: 20px; border-bottom: 1px solid var(--border); }
        .sidebar-header h1 { font-size: 1.3rem; color: var(--accent-gold); display: flex; align-items: center; gap: 8px; }
        .sidebar-header p { font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }
        .search-box { padding: 12px 20px; border-bottom: 1px solid var(--border); }
        .search-box input { width: 100%; padding: 8px 12px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; color: #fff; font-size: 0.85rem; }
        .tablet-list { flex: 1; overflow-y: auto; list-style: none; }
        .tablet-item { padding: 12px 20px; border-bottom: 1px solid rgba(255,255,255,0.05); cursor: pointer; transition: background 0.15s; }
        .tablet-item:hover, .tablet-item.active { background: var(--bg-card); }
        .item-id { font-weight: bold; color: var(--accent-cyan); font-size: 0.95rem; }
        .item-meta { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }
        .badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; }
        .badge-clean { background: rgba(74, 222, 128, 0.15); color: var(--accent-green); }
        .badge-error { background: rgba(248, 113, 113, 0.15); color: var(--accent-red); }
        .badge-date { background: rgba(251, 191, 36, 0.15); color: var(--accent-gold); }

        /* Main Workspace */
        #workspace { flex: 1; display: flex; flex-direction: column; overflow-y: auto; background: var(--bg-primary); }
        .workspace-header { padding: 20px 30px; background: var(--bg-secondary); border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .header-title h2 { font-size: 1.5rem; color: #fff; }
        .header-title p { font-size: 0.85rem; color: var(--text-muted); }
        
        .content-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; padding: 30px; }
        
        .panel { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
        .panel h3 { font-size: 1.05rem; margin-bottom: 16px; color: var(--accent-cyan); border-bottom: 1px solid var(--border); padding-bottom: 8px; }
        
        /* Transliteration */
        .surface-title { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: var(--accent-gold); margin: 12px 0 6px 0; }
        .line-row { display: flex; gap: 12px; font-family: "Courier New", Courier, monospace; font-size: 0.9rem; padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.02); }
        .line-no { color: var(--text-muted); width: 35px; text-align: right; user-select: none; }
        .line-text { color: #e2e8f0; flex: 1; }
        .tok-num { color: var(--accent-gold); font-weight: bold; }
        .tok-official { color: var(--accent-cyan); text-decoration: underline; }
        .tok-broken { color: var(--accent-red); opacity: 0.8; }
        .tok-comm { color: var(--accent-green); }

        /* CDLI Image Section */
        .photo-container { text-align: center; }
        .photo-container img { max-width: 100%; border-radius: 6px; border: 1px solid var(--border); margin-bottom: 8px; background: #000; }
        .cdli-link { display: inline-block; font-size: 0.8rem; color: var(--accent-cyan); text-decoration: none; margin-top: 8px; }
        .cdli-link:hover { text-decoration: underline; }

        /* Status Cards */
        .status-box { padding: 12px; border-radius: 6px; margin-bottom: 14px; font-size: 0.85rem; }
        .box-clean { background: rgba(74, 222, 128, 0.1); border: 1px solid rgba(74, 222, 128, 0.3); color: #86efac; }
        .box-issues { background: rgba(248, 113, 113, 0.1); border: 1px solid rgba(248, 113, 113, 0.3); color: #fca5a5; }
        .box-chronos { background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); color: #7dd3fc; }
        
        .meta-list { list-style: none; font-size: 0.85rem; }
        .meta-list li { padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; }
        .meta-list span.val { font-weight: bold; color: #fff; }
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="sidebar-header">
            <h1>📜 Nisaba Browser</h1>
            <p>Ur III Cuneiform Visual Explorer</p>
        </div>
        <div class="search-box">
            <input type="text" id="filterInput" placeholder="Filter P-number (e.g. P100001)..." onkeyup="filterTablets()">
        </div>
        <ul class="tablet-list" id="tabletList">
            {% for t in tablets %}
            <li class="tablet-item {% if loop.first %}active{% endif %}" onclick="selectTablet('{{ t.id_text }}')" id="item-{{ t.id_text }}">
                <div class="item-id">{{ t.id_text }} <span class="badge badge-date">{{ t.date_code or 'Undated' }}</span></div>
                <div class="item-meta">{{ t.designation }} • {{ t.line_count }} lines</div>
            </li>
            {% endfor %}
        </ul>
    </div>

    <div id="workspace">
        {% for t in tablets %}
        <div class="tablet-view" id="view-{{ t.id_text }}" style="{% if not loop.first %}display:none;{% endif %}">
            <div class="workspace-header">
                <div class="header-title">
                    <h2>{{ t.id_text }} — {{ t.designation }}</h2>
                    <p>{{ t.period }} • {{ t.provenance }}</p>
                </div>
                <div>
                    <a class="cdli-link" href="https://cdli.mpiwg-berlin.mpg.de/artifacts/{{ t.id_text }}" target="_blank">🌐 Open on CDLI Database ↗</a>
                </div>
            </div>

            <div class="content-grid">
                <!-- Column 1: Transliteration -->
                <div class="panel">
                    <h3>📝 ATF Transliteration</h3>
                    {% for surf, lines in t.surfaces.items() %}
                    <div class="surface-title">@{{ surf }}</div>
                    {% for l in lines %}
                    <div class="line-row">
                        <span class="line-no">{{ l.line_label }}.</span>
                        <span class="line-text">{{ l.highlighted_text | safe }}</span>
                    </div>
                    {% endfor %}
                    {% endfor %}
                </div>

                <!-- Column 2: Analytics, Dates & Image -->
                <div>
                    <div class="panel" style="margin-bottom: 24px;">
                        <h3>🏛️ Chronos & Verification</h3>
                        <div class="status-box box-chronos">
                            <strong>Macro-Chronology:</strong> {{ t.chronos_status }}<br>
                            <strong>Resolved Date:</strong> {{ t.date_code or 'Pending Resolution' }} (Confidence: {{ t.date_confidence }})
                        </div>
                        <div class="status-box box-clean" style="border-color: rgba(56, 189, 248, 0.4); background: rgba(56, 189, 248, 0.08);">
                            <strong>✍️ Scribe / Author:</strong> {{ t.author_name or 'Unattributed' }}<br>
                            <span style="font-size: 0.8rem; color: var(--text-muted);">Title: {{ t.author_title }} • Patronymic: {{ t.author_father }} • Conf: {{ t.author_conf }}</span>
                        </div>
                        {% if t.lint_issues %}
                        <div class="status-box box-issues">
                            <strong>⚠️ Linter Findings ({{ t.lint_issues | length }}):</strong>
                            <ul style="margin-left: 18px; margin-top: 4px;">
                                {% for iss in t.lint_issues %}
                                <li>[{{ iss.rule_id }}] line {{ iss.line_number }}: {{ iss.message }}</li>
                                {% endfor %}
                            </ul>
                        </div>
                        {% else %}
                        <div class="status-box box-clean">
                            ✅ <strong>Linter Status:</strong> 100% Valid C-ATF (Clean parity, valid tokens)
                        </div>
                        {% endif %}

                        <ul class="meta-list">
                            <li><span>Attested Officials:</span> <span class="val">{{ t.officials | join(', ') or 'None' }}</span></li>
                            <li><span>Commodity Transactions:</span> <span class="val">{{ t.transactions_count }}</span></li>
                            <li><span>Candidate Joins:</span> <span class="val">{{ t.joins_count }} match(es)</span></li>
                        </ul>
                    </div>

                    <div class="panel photo-container">
                        <h3>📷 Tablet Artifact Archive</h3>
                        <img src="../assets/real_tablets/{{ t.id_text }}.jpg" alt="Tablet photo {{ t.id_text }}" onerror="this.onerror=null; this.src='https://cdli.earth/dl/photo/{{ t.id_text }}.jpg';">
                        <div>
                            <a class="cdli-link" href="https://cdli.earth/dl/photo/{{ t.id_text }}.jpg" target="_blank">🔍 View Full Resolution Scan ↗</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <script>
        function selectTablet(id) {
            document.querySelectorAll('.tablet-view').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tablet-item').forEach(el => el.classList.remove('active'));
            const view = document.getElementById('view-' + id);
            const item = document.getElementById('item-' + id);
            if (view) view.style.display = 'block';
            if (item) item.classList.add('active');
        }

        function filterTablets() {
            const query = document.getElementById('filterInput').value.toLowerCase();
            document.querySelectorAll('.tablet-item').forEach(item => {
                const text = item.innerText.toLowerCase();
                item.style.display = text.includes(query) ? 'block' : 'none';
            });
        }

        window.addEventListener('DOMContentLoaded', () => {
            const hash = window.location.hash.replace('#', '');
            if (hash) {
                selectTablet(hash);
            }
        });
    </script>
</body>
</html>
"""


class TabletBrowserRenderer:
    """Renders self-contained interactive HTML explorer for parsed tablets."""

    @staticmethod
    def _highlight_line(text: str) -> str:
        """Adds HTML span highlighting to transliteration tokens."""
        tokens = text.split()
        res = []
        for raw_tok in tokens:
            tok = html.escape(raw_tok)
            if re.match(r"^\d+\([a-z0-9\']+\)", raw_tok):
                res.append(f'<span class="tok-num">{tok}</span>')
            elif raw_tok in ("udu", "masz2", "sila4", "u8", "gu4", "ab2", "sze", "dabin"):
                res.append(f'<span class="tok-comm">{tok}</span>')
            elif "[" in raw_tok or "]" in raw_tok or "#" in raw_tok or "x" in raw_tok:
                res.append(f'<span class="tok-broken">{tok}</span>')
            elif raw_tok.startswith("ki-") or "i3-dab5" in raw_tok or "kiszib3" in raw_tok:
                res.append(f'<span class="tok-official">{tok}</span>')
            else:
                res.append(tok)
        return " ".join(res)

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
        """Compiles tablet data into an interactive HTML application."""
        os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)

        # Index estimates by id_text
        est_map = {e.id_text: e for e in (estimates or [])}
        attr_map = {a.id_text: a for a in (attributions or [])}

        # Index linter issues by id_text
        lint_map = {}
        if linter_report:
            for iss in linter_report.issues:
                lint_map.setdefault(iss.id_text, []).append(iss)

        # Index joins by id_text
        joins_count_map = {}
        if joins:
            for j in joins:
                joins_count_map[j.id_text_a] = joins_count_map.get(j.id_text_a, 0) + 1
                joins_count_map[j.id_text_b] = joins_count_map.get(j.id_text_b, 0) + 1

        # Index transactions by id_text
        tx_count_map = {}
        if transactions:
            for tx in transactions:
                tx_count_map[tx.id_text] = tx_count_map.get(tx.id_text, 0) + 1

        view_tablets = []
        for tab in tablets:
            est = est_map.get(tab.id_text)
            date_code = est.resolved_year if est else None
            chronos_status = est.status if est else "UNEVALUATED"
            date_conf = f"{int((est.confidence or 0.0) * 100)}%" if est else "N/A"

            attr = attr_map.get(tab.id_text)
            author_name = attr.identified_scribe if attr else None
            author_title = attr.title or "dub-sar" if attr else "N/A"
            author_father = attr.patronymic or "Unrecorded" if attr else "N/A"
            author_conf = f"{int((attr.confidence or 0.0) * 100)}%" if attr else "N/A"

            surfaces: Dict[str, List[dict]] = {}
            officials_set = set()

            for line in tab.lines:
                surfaces.setdefault(line.surface, []).append({
                    "line_label": line.line_label,
                    "raw_text": line.raw_text,
                    "highlighted_text": self._highlight_line(line.raw_text),
                })
                # Check for officials
                if "ki " in line.raw_text or "i3-dab5" in line.raw_text or "kiszib3" in line.raw_text:
                    for tok in line.normalized_text.split():
                        if tok not in ("ki", "i3-dab5", "kiszib3", "ba-zi", "ta"):
                            officials_set.add(tok)

            view_tablets.append({
                "id_text": tab.id_text,
                "designation": tab.designation,
                "period": tab.period,
                "provenance": tab.provenance,
                "line_count": len(tab.lines),
                "date_code": date_code,
                "chronos_status": chronos_status,
                "date_confidence": date_conf,
                "author_name": author_name,
                "author_title": author_title,
                "author_father": author_father,
                "author_conf": author_conf,
                "officials": sorted(list(officials_set))[:5],
                "lint_issues": lint_map.get(tab.id_text, []),
                "joins_count": joins_count_map.get(tab.id_text, 0),
                "transactions_count": tx_count_map.get(tab.id_text, 0),
                "surfaces": surfaces,
            })

        template = Template(HTML_TEMPLATE)
        html_content = template.render(tablets=view_tablets)

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_filepath
