"""Tests for LedgerExtractor and LedgerAuditor."""

import pytest
from src.compiler.parser import ATFParser
from src.ledger.extractor import LedgerExtractor
from src.ledger.auditor import LedgerAuditor


def test_ledger_extraction_and_balances():
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    extractor = LedgerExtractor()
    transactions = extractor.extract_corpus(tablets)

    assert len(transactions) > 0

    # Check P100002: 3 udu, 2 masz2, ki ab-ba-sa6-ga-ta na-lu5 i3-dab5
    t2_txs = [tx for tx in transactions if tx.id_text == "P100002"]
    assert len(t2_txs) >= 2
    assert any(tx.commodity == "udu" and tx.quantity == 3.0 for tx in t2_txs)
    assert any(tx.commodity == "masz2" and tx.quantity == 2.0 for tx in t2_txs)
    assert all(tx.source_party == "ab-ba-sa6-ga" for tx in t2_txs)
    assert all(tx.receiving_party == "na-lu5" for tx in t2_txs)

    # Test Auditor
    auditor = LedgerAuditor()
    balances = auditor.compute_balances(transactions)
    assert len(balances) > 0

    # Na-lu5 received animals
    nalu_bal = [b for b in balances if b.officer == "na-lu5"]
    assert len(nalu_bal) > 0
    assert any(b.commodity == "udu" and b.total_received == 3.0 for b in nalu_bal)
