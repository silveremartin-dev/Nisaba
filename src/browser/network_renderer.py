"""
Interactive Visual Renderer for Prosopographic Social Networks.
Generates a standalone, dark-themed HTML graph app powered by Cytoscape.js
with node inspector, community color coding, betweenness ranking, and instant search.
"""

import json
import os
from typing import Any, Dict, Optional
from src.chronos.network import ProsopographicNetwork


class NetworkGraphRenderer:
    """Renders prosopographic administrative graphs into responsive standalone HTML applications."""

    def render_network_html(
        self,
        network: ProsopographicNetwork,
        output_filepath: str = "data/processed/prosopography_graph.html",
        min_weight: int = 1,
        max_nodes: int = 200,
    ) -> str:
        """Exports an interactive Cytoscape.js HTML graph visualization."""
        os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)

        cy_data = network.to_cytoscape_json(min_weight=min_weight, max_nodes=max_nodes)
        top_influencers = network.get_top_influencers(top_n=12)

        data_json = json.dumps(cy_data["elements"], ensure_ascii=False).replace("</", "<\\/")
        top_json = json.dumps(top_influencers, ensure_ascii=False).replace("</", "<\\/")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nisaba Prosopography Network Explorer</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: #131b2e;
      --border: #233554;
      --accent: #38bdf8;
      --gold: #fbbf24;
      --green: #34d399;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }}
    body {{ background: var(--bg); color: var(--text); height: 100vh; overflow: hidden; display: flex; flex-direction: column; }}
    
    header {{
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 10;
    }}
    .logo {{ font-size: 1.25rem; font-weight: 800; letter-spacing: 1px; color: var(--accent); display: flex; align-items: center; gap: 8px; }}
    .badge {{ background: #0369a1; color: #e0f2fe; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; }}
    .stats-bar {{ display: flex; gap: 20px; font-size: 0.85rem; color: var(--text-muted); }}
    .stats-bar span strong {{ color: var(--gold); }}

    .main-container {{ display: flex; flex: 1; height: calc(100vh - 65px); }}
    
    #cy {{ flex: 1; height: 100%; background: radial-gradient(circle at center, #111827 0%, #0b0f19 100%); }}

    aside {{
      width: 380px;
      background: var(--card-bg);
      border-left: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow-y: auto;
    }}
    .panel-section {{ padding: 16px; border-bottom: 1px solid var(--border); }}
    .panel-title {{ font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--accent); margin-bottom: 12px; }}

    .search-input {{
      width: 100%;
      background: #0b0f19;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.85rem;
      outline: none;
    }}
    .search-input:focus {{ border-color: var(--accent); }}

    .node-card {{
      background: #0b0f19;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      margin-top: 8px;
    }}
    .node-title {{ font-size: 1.1rem; font-weight: 700; color: var(--gold); margin-bottom: 4px; }}
    .node-role {{ font-size: 0.8rem; color: var(--green); text-transform: uppercase; margin-bottom: 8px; }}
    .metric-row {{ display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px; color: var(--text-muted); }}
    .metric-row strong {{ color: var(--text); }}
    .pill-list {{ display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }}
    .pill {{ background: #1e293b; color: #38bdf8; font-size: 0.7rem; padding: 2px 6px; border-radius: 3px; }}

    .rank-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 8px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.82rem;
      transition: background 0.15s;
    }}
    .rank-item:hover {{ background: #1e293b; }}
    .rank-name {{ color: var(--text); font-weight: 600; }}
    .rank-score {{ color: var(--accent); font-family: monospace; }}

    .controls {{ display: flex; gap: 8px; margin-top: 10px; }}
    .btn {{
      background: #1e293b;
      color: var(--text);
      border: 1px solid var(--border);
      padding: 6px 12px;
      border-radius: 4px;
      font-size: 0.8rem;
      cursor: pointer;
    }}
    .btn:hover {{ background: var(--accent); color: #0b0f19; }}

    .tab-link {{
      background: #1e293b;
      border: 1px solid #38bdf8;
      color: #38bdf8;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-family: monospace;
      text-decoration: none;
      font-weight: 600;
      display: inline-block;
      margin: 2px;
      transition: all 0.15s;
    }}
    .tab-link:hover {{
      background: #0284c7;
      color: #fff;
      border-color: #7dd3fc;
    }}
  </style>
</head>
<body>
  <header>
    <div class="logo">
      <span>NISABA</span>
      <span class="badge">Prosopography Engine</span>
    </div>
    <div class="stats-bar">
      <span>Officials: <strong id="stat-nodes">{cy_data['summary']['total_nodes']}</strong></span>
      <span>Bureaucratic Links: <strong id="stat-edges">{cy_data['summary']['total_edges']}</strong></span>
      <span>Chancelleries/Clusters: <strong id="stat-comms">{cy_data['summary']['communities']}</strong></span>
    </div>
  </header>

  <div class="main-container">
    <div id="cy"></div>

    <aside>
      <div class="panel-section">
        <div class="panel-title">Search & Filter</div>
        <input type="text" id="searchInput" class="search-input" placeholder="Search official or scribe (e.g. lu2-kal-la)...">
        <div class="controls">
          <button class="btn" id="btnFit">Reset View</button>
          <button class="btn" id="btnRelayout">Re-Layout</button>
        </div>
      </div>

      <div class="panel-section">
        <div class="panel-title">Inspector Card</div>
        <div id="inspector">
          <p style="color: var(--text-muted); font-size: 0.85rem;">Click any node to inspect official profile, centrality metrics, and administrative tablets.</p>
        </div>
      </div>

      <div class="panel-section" style="flex: 1;">
        <div class="panel-title">Top Central Chancellery Figures</div>
        <div id="rankList"></div>
      </div>
    </aside>
  </div>

  <script>
    const elementsData = {data_json};
    const topFigures = {top_json};

    const commColors = [
      '#38bdf8', '#fbbf24', '#34d399', '#f43f5e', '#a855f7',
      '#fb923c', '#4ade80', '#2dd4bf', '#818cf8', '#f472b6'
    ];

    const cy = cytoscape({{
      container: document.getElementById('cy'),
      elements: elementsData,
      style: [
        {{
          selector: 'node',
          style: {{
            'label': 'data(label)',
            'color': '#f1f5f9',
            'font-size': '10px',
            'text-valign': 'bottom',
            'text-margin-y': 5,
            'background-color': function(ele) {{
              const comm = ele.data('community') || 0;
              return commColors[comm % commColors.length];
            }},
            'width': function(ele) {{
              return Math.max(16, Math.min(50, 16 + (ele.data('degree') || 0) * 3));
            }},
            'height': function(ele) {{
              return Math.max(16, Math.min(50, 16 + (ele.data('degree') || 0) * 3));
            }},
            'border-width': 1.5,
            'border-color': '#ffffff'
          }}
        }},
        {{
          selector: 'edge',
          style: {{
            'width': function(ele) {{
              return Math.max(1, Math.min(8, (ele.data('weight') || 1) * 1.2));
            }},
            'line-color': '#334155',
            'curve-style': 'bezier',
            'opacity': 0.6
          }}
        }},
        {{
          selector: '.highlighted',
          style: {{
            'border-color': '#fbbf24',
            'border-width': 4,
            'line-color': '#fbbf24',
            'opacity': 1.0,
            'z-index': 999
          }}
        }},
        {{
          selector: '.dimmed',
          style: {{
            'opacity': 0.15
          }}
        }}
      ],
      layout: {{
        name: 'cose',
        animate: false,
        randomize: false,
        componentSpacing: 100,
        nodeOverlap: 20,
        idealEdgeLength: 60
      }}
    }});

    const BASE_EXPLORER = (window.location.protocol === 'file:') ? 'browser.html' : '/explorer';

    function openTablet(tabletId) {{
      if (window.parent && window.parent.selectTabletFromGraph) {{
        window.parent.selectTabletFromGraph(tabletId);
      }} else {{
        window.location.href = BASE_EXPLORER + '#' + tabletId;
      }}
    }}

    function inspectNode(node) {{
      const d = node.data();
      const col = commColors[(d.community || 0) % commColors.length];
      const tabs = (d.sample_tablets && d.sample_tablets.length > 0)
        ? d.sample_tablets.map(t => `<span class="tab-link" onclick="openTablet('${{t}}')" style="cursor:pointer;">${{t}}</span>`).join(' ')
        : '<span style="color:var(--text-muted); font-size:0.8rem;">Historical Ur III transaction official</span>';

      document.getElementById('inspector').innerHTML = `
        <div class="node-card" style="border-top: 3px solid ${{col}};">
          <div class="node-title">${{d.label}}</div>
          <div class="node-role">${{d.role || 'Official'}} &bull; Cluster #${{d.community}}</div>
          <div class="metric-row"><span>Total Tablets:</span> <strong>${{(d.tablet_count || 0).toLocaleString()}}</strong></div>
          <div class="metric-row"><span>Bureaucratic Partners:</span> <strong>${{d.degree}}</strong></div>
          <div class="metric-row"><span>Betweenness Centrality:</span> <strong>${{d.betweenness}}</strong></div>
          
          <div style="margin-top: 12px; font-size: 0.8rem; font-weight: 700; color: var(--accent);">
            Key Attested Tablets (Click to inspect):
          </div>
          <div style="margin-top: 6px;">
            ${{tabs}}
          </div>

          <div style="margin-top: 14px; display: flex; flex-direction: column; gap: 6px;">
            <button onclick="if(window.parent&&window.parent.filterBySearch){{window.parent.filterBySearch('${{d.label}}'); window.parent.switchView('dossier');}}else{{window.location.href='${{BASE_EXPLORER}}?search=${{encodeURIComponent(d.label)}}';}}" class="btn" style="text-align: center; text-decoration: none; display: block; width: 100%;">
              🏺 View All Tablets for ${{d.label}}
            </button>
          </div>
        </div>
      `;

      cy.elements().removeClass('highlighted dimmed');
      const neighborhood = node.neighborhood().add(node);
      cy.elements().difference(neighborhood).addClass('dimmed');
      neighborhood.addClass('highlighted');
    }}

    cy.on('tap', 'node', function(evt) {{
      inspectNode(evt.target);
    }});

    cy.on('tap', 'edge', function(evt) {{
      const e = evt.target.data();
      const edgeTabs = (e.tablets && e.tablets.length > 0)
        ? e.tablets.map(t => `<span class="tab-link" onclick="openTablet('${{t}}')" style="cursor:pointer;">${{t}}</span>`).join(' ')
        : 'Attested in archival transactions';

      document.getElementById('inspector').innerHTML = `
        <div class="node-card" style="border-top: 3px solid var(--gold);">
          <div class="node-title">${{e.source}} ↔ ${{e.target}}</div>
          <div class="node-role">Bureaucratic Transfer Flow</div>
          <div class="metric-row"><span>Recorded Transactions:</span> <strong>${{(e.weight || 0).toLocaleString()}}</strong></div>
          <div style="margin-top: 12px; font-size: 0.8rem; font-weight: 700; color: var(--accent);">
            Corroborating Tablets:
          </div>
          <div style="margin-top: 6px;">
            ${{edgeTabs}}
          </div>
          <div style="margin-top: 14px;">
            <button onclick="if(window.parent&&window.parent.filterBySearch){{window.parent.filterBySearch('${{e.source}}'); window.parent.switchView('dossier');}}else{{window.location.href='${{BASE_EXPLORER}}?search=${{encodeURIComponent(e.source)}}';}}" class="btn" style="text-align: center; text-decoration: none; display: block; width: 100%;">
              🏺 Explore Transactions in Tablet Dossier
            </button>
          </div>
        </div>
      `;
    }});

    cy.on('tap', function(evt) {{
      if (evt.target === cy) {{
        cy.elements().removeClass('highlighted dimmed');
      }}
    }});

    // Populate Top Figures list
    const rankContainer = document.getElementById('rankList');
    topFigures.forEach((fig, i) => {{
      const div = document.createElement('div');
      div.className = 'rank-item';
      div.innerHTML = `
        <span class="rank-name">${{i+1}}. ${{fig.name}} <small style="color:var(--text-muted);">(${{fig.role}})</small></span>
        <span class="rank-score">${{fig.degree}} links</span>
      `;
      div.onclick = () => {{
        const target = cy.getElementById(fig.name);
        if (target && target.length > 0) {{
          cy.animate({{ center: {{ eles: target }}, zoom: 1.8 }}, {{ duration: 500 }});
          inspectNode(target);
        }}
      }};
      rankContainer.appendChild(div);
    }});

    // Search filter
    document.getElementById('searchInput').addEventListener('input', (e) => {{
      const val = e.target.value.toLowerCase().trim();
      if (!val) {{
        cy.elements().removeClass('highlighted dimmed');
        return;
      }}
      const matches = cy.nodes().filter(n => n.data('label').toLowerCase().includes(val));
      if (matches.length > 0) {{
        cy.elements().addClass('dimmed');
        matches.removeClass('dimmed').addClass('highlighted');
        matches.neighborhood().removeClass('dimmed');
        if (matches.length === 1) {{
          inspectNode(matches[0]);
          cy.animate({{ center: {{ eles: matches[0] }}, zoom: 1.5 }}, {{ duration: 400 }});
        }}
      }}
    }});

    document.getElementById('btnFit').addEventListener('click', () => {{
      cy.elements().removeClass('highlighted dimmed');
      cy.fit();
    }});

    document.getElementById('btnRelayout').addEventListener('click', () => {{
      cy.layout({{ name: 'cose', animate: true, animationDuration: 600 }}).run();
    }});
  </script>
</body>
</html>
"""
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_filepath
