"""
Tests for Prosopographic Network and NetworkGraphRenderer.
Verifies network graph construction, centrality, communities, Cytoscape/D3 exports, and HTML generation.
"""

import os
import tempfile
import pytest

from src.compiler.parser import ATFParser
from src.chronos.network import ProsopographicNetwork
from src.browser.network_renderer import NetworkGraphRenderer


def test_prosopographic_network_construction():
    sample_atf = "data/raw/sample_cdli.atf"
    assert os.path.exists(sample_atf)

    parser = ATFParser()
    tablets = parser.parse_file(sample_atf)
    assert len(tablets) > 0

    net = ProsopographicNetwork()
    g = net.build_network(tablets, min_co_occurrences=1)

    assert len(g.nodes) > 0
    # Check top influencers
    top = net.get_top_influencers(top_n=5)
    assert len(top) > 0
    assert "name" in top[0]
    assert "degree" in top[0]
    assert "betweenness_centrality" in top[0]
    assert "community_id" in top[0]

    # Test Cytoscape JSON export
    cy = net.to_cytoscape_json(min_weight=1, max_nodes=50)
    assert "elements" in cy
    assert "nodes" in cy["elements"]
    assert "edges" in cy["elements"]
    assert "summary" in cy

    # Test D3 JSON export
    d3 = net.to_d3_json(min_weight=1, max_nodes=50)
    assert "nodes" in d3
    assert "links" in d3
    assert len(d3["nodes"]) == len(cy["elements"]["nodes"])


def test_network_graph_renderer():
    sample_atf = "data/raw/sample_cdli.atf"
    parser = ATFParser()
    tablets = parser.parse_file(sample_atf)

    net = ProsopographicNetwork()
    net.build_network(tablets)

    renderer = NetworkGraphRenderer()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_html = os.path.join(tmpdir, "test_network.html")
        rendered = renderer.render_network_html(net, output_filepath=out_html)

        assert os.path.exists(rendered)
        with open(rendered, "r", encoding="utf-8") as f:
            content = f.read()

        assert "cytoscape" in content
        assert "Inspector Card" in content
        assert "Top Central Chancellery Figures" in content
        assert "NISABA" in content
