"""Tests for Ur III taxonomy, king chronological order, and metrology."""

import pytest
from src.chronos.year_names import YEAR_CATALOG


def test_taxonomy_kings():
    kings = {yf.king for yf in YEAR_CATALOG}
    assert "SH" in kings
    assert "AS" in kings
    assert "SS" in kings
    assert "IS" in kings


def test_taxonomy_year_codes_unique():
    codes = [yf.code for yf in YEAR_CATALOG]
    assert len(codes) == len(set(codes)), "Duplicate year code detected in catalog"


def test_metrology_conversions():
    # 1(gur) = 300 sila3, 1(barig) = 60 sila3, 1(ban2) = 10 sila3
    from src.ledger.extractor import LedgerExtractor
    extractor = LedgerExtractor()
    assert extractor._parse_quantity("1(disz)") == 1.0
    assert extractor._parse_quantity("2(u)") == 20.0
    assert extractor._parse_quantity("1(gesz2)") == 60.0
