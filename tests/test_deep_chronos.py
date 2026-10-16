"""Deep tests for Chronos-Graph year normalization and Bayesian date inference."""

import pytest
from src.chronos.year_names import YearNormalizer, YEAR_CATALOG
from src.chronos.solver import ChronosSolver
from src.compiler.parser import TabletRecord, LineRecord


def test_year_catalog_coverage():
    norm = YearNormalizer()

    # Shulgi 44
    assert norm.normalize("mu si-mu-ru-um{ki} lu-lu-bu{ki} a-ra2 1(u) la2 1(disz)-kam-asz ba-hul").code == "SH44"
    # Amar-Suen 01
    assert norm.normalize("mu {d}amar-{d}suen lugal").code == "AS01"
    # Shu-Suen 04 (Bad-Mar-tu)
    assert norm.normalize("mu bad3 mar-tu mu-ri-iq-ti-id-ni-im mu-du3").code == "SS04"
    # Ibbi-Suen 01
    assert norm.normalize("mu {d}i-bi2-{d}suen lugal").code == "IS01"


def test_chronos_disjoint_window_handling():
    # Synthetic tablet with no entities
    tab = TabletRecord(id_text="P_EMPTY", designation="EMPTY 1", lines=[
        LineRecord("P_EMPTY_1", "P_EMPTY", "obverse", 1, "1", "1(disz) udu", "1(disz) udu", False, [])
    ])

    solver = ChronosSolver()
    estimates = solver.fit_and_resolve([tab])
    assert len(estimates) == 1
    est = estimates[0]
    assert est.status == "UNDETERMINED"
    assert est.confidence == 0.0
