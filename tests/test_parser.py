"""Tests for ATFParser AST building and sign classification."""

import pytest
from src.compiler.parser import ATFParser


def test_parser_sample_tablet():
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    assert len(tablets) == 15
    t1 = tablets[0]
    assert t1.id_text == "P100001"
    assert t1.designation == "AAS 001"
    assert t1.has_date is True
    assert len(t1.lines) == 10  # 4 obv, 3 rev, 3 seal

    # Verify line 1
    l1 = t1.lines[0]
    assert l1.surface == "obverse"
    assert l1.line_number == 1
    assert l1.raw_text == "1(disz) udu niga"
    assert len(l1.signs) == 3

    # Check sign classification
    s1, s2, s3 = l1.signs
    assert s1.sign_type == "NUMERIC"
    assert s1.clean_value == "1(disz)"

    assert s2.clean_value == "udu"
    assert s3.clean_value == "niga"


def test_parser_damaged_signs():
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    t7 = tablets[6]  # P100007 has [ ... ] 1(disz) udu niga and 1(disz) u8#
    assert t7.id_text == "P100007"
    l2 = t7.lines[1]
    assert l2.is_damaged is True
    assert any(s.damage_flag == "#" for s in l2.signs)
