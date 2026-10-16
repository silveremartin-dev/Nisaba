"""Tests for TabletBrowserRenderer."""

import os
import pytest
from src.compiler.parser import ATFParser
from src.browser.renderer import TabletBrowserRenderer


def test_browser_renderer_output(tmp_path):
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    renderer = TabletBrowserRenderer()
    out_html = str(tmp_path / "test_browser.html")
    res_path = renderer.render_corpus(tablets=tablets, output_filepath=out_html)

    assert os.path.exists(res_path)
    with open(res_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert "P100001" in html
    assert "Nisaba" in html
    assert "P100001.jpg" in html
    assert "tok-num" in html
