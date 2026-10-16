"""Tests for YearNormalizer, ProsopographyExtractor, and ChronosSolver."""

import pytest
from src.compiler.parser import ATFParser
from src.chronos.year_names import YearNormalizer
from src.chronos.prosopography import ProsopographyExtractor
from src.chronos.solver import ChronosSolver


def test_year_normalizer():
    norm = YearNormalizer()

    # Exact match
    y1 = norm.normalize("mu {d}amar-{d}suen lugal-e ur-bi2-lum{ki} mu-hul")
    assert y1 is not None
    assert y1.code == "AS02"

    # Match with damage brackets
    y2 = norm.normalize("mu en-mah-gal-an-na en {d}nanna ba-hun")
    assert y2 is not None
    assert y2.code == "AS04"

    # Substring match
    y3 = norm.normalize("mu ma-da za-ab-sza-li{ki} mu-hul")
    assert y3 is not None
    assert y3.code == "SS07"

    # Damaged with no content
    y4 = norm.normalize("mu [ ... ]")
    assert y4 is None


def test_chronos_solver_undated_tablet():
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    solver = ChronosSolver()
    estimates = solver.fit_and_resolve(tablets)

    assert len(estimates) == 7

    # P100001 has certified date
    e1 = next(e for e in estimates if e.id_text == "P100001")
    assert e1.status == "CERTIFIED_DATED"
    assert e1.confidence == 1.0

    # P100004 has mu [ ... ], but mentions ab-ba-sa6-ga and ur-szu-ga-lam-ma
    e4 = next(e for e in estimates if e.id_text == "P100004")
    assert e4.status == "ESTIMATED"
    assert e4.confidence > 0.0
    assert any("AS" in c for c in e4.candidate_years)
