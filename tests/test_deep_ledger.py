"""Deep edge case tests for Ur III Ledger and commodity balance sheets."""

import pytest
from src.compiler.parser import TabletRecord, LineRecord, SignRecord
from src.ledger.extractor import LedgerExtractor, TransactionRecord
from src.ledger.auditor import LedgerAuditor


def test_ledger_sexagesimal_capacity():
    extractor = LedgerExtractor()
    # 1(disz) = 1, 1(u) = 10, 1(gesz2) = 60
    assert extractor._parse_quantity("1(disz)") == 1.0
    assert extractor._parse_quantity("3(disz)") == 3.0
    assert extractor._parse_quantity("2(u)") == 20.0
    assert extractor._parse_quantity("5(u)") == 50.0
    assert extractor._parse_quantity("1(gesz2)") == 60.0
    assert extractor._parse_quantity("2(gesz2)") == 120.0


def test_ledger_multi_commodity_tablet():
    lines = [
        LineRecord("P99_obv_1", "P99", "obverse", 1, "1", "10(disz) udu", "10(disz) udu", False, []),
        LineRecord("P99_obv_2", "P99", "obverse", 2, "2", "5(disz) masz2-gal", "5(disz) masz2-gal", False, []),
        LineRecord("P99_obv_3", "P99", "obverse", 3, "3", "ki ur-mes-ta", "ki ur-mes-ta", False, []),
        LineRecord("P99_rev_1", "P99", "reverse", 1, "1", "in-ta-e3-a i3-dab5", "in-ta-e3-a i3-dab5", False, []),
    ]
    tab = TabletRecord(id_text="P99", designation="TEST 99", lines=lines)

    extractor = LedgerExtractor()
    txs = extractor.extract_transactions(tab)

    assert len(txs) == 2
    assert txs[0].quantity == 10.0
    assert txs[0].commodity == "udu"
    assert txs[0].source_party == "ur-mes"
    assert txs[0].receiving_party == "in-ta-e3-a"

    assert txs[1].quantity == 5.0
    assert txs[1].commodity == "masz2-gal"
    assert txs[1].source_party == "ur-mes"
    assert txs[1].receiving_party == "in-ta-e3-a"

    # Test Auditor balances
    auditor = LedgerAuditor()
    balances = auditor.compute_balances(txs)

    # in-ta-e3-a received 10 udu, 5 masz2-gal
    inta_udu = next(b for b in balances if b.officer == "in-ta-e3-a" and b.commodity == "udu")
    assert inta_udu.total_received == 10.0
    assert inta_udu.total_expended == 0.0
    assert inta_udu.net_inventory == 10.0

    # ur-mes expended 10 udu
    urmes_udu = next(b for b in balances if b.officer == "ur-mes" and b.commodity == "udu")
    assert urmes_udu.total_received == 0.0
    assert urmes_udu.total_expended == 10.0
    assert urmes_udu.net_inventory == -10.0
