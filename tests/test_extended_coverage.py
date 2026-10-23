"""
Extended comprehensive unit and integration test suite for Nisaba.
Adds 25 rigorous tests covering epigraphic AST parsing, lexer edge cases,
double-entry conservation invariants, k-mer metrics, Bayesian chronos,
linter validation, and API edge cases.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from src.compiler.lexer import ATFLexer, TokenType
from src.compiler.parser import ATFParser, SignRecord, LineRecord, TabletRecord
from src.ledger.extractor import LedgerExtractor
from src.ledger.auditor import LedgerAuditor
from src.joins.kmer import KmerIndexer
from src.chronos.solver import ChronosSolver
from src.linter.bracket_auditor import BracketAuditor, IssueSeverity
from src.storage.chunker import FileSharder
from src.chronos.year_names import YEAR_CATALOG
from src.api.app import app


# ---------------------------------------------------------------------------
# 1. Lexer Edge Cases
# ---------------------------------------------------------------------------

def test_lexer_empty_input():
    lexer = ATFLexer()
    tokens = list(lexer.tokenize_stream(iter([])))
    assert len(tokens) == 0


def test_lexer_comment_and_language_stream():
    lexer = ATFLexer()
    lines = ["# comment one\n", "#atf: lang sux\n", "# comment two\n"]
    tokens = list(lexer.tokenize_stream(iter(lines)))
    assert len(tokens) == 3
    assert tokens[0].type == TokenType.COMMENT
    assert tokens[1].type == TokenType.LANGUAGE
    assert tokens[2].type == TokenType.COMMENT


def test_lexer_primed_line_numbers():
    lexer = ATFLexer()
    lines = [
        "&P100999 = Test Prime\n",
        "@obverse\n",
        "1'. 2(disz) udu\n",
        "2''. 1(disz) masz2\n",
    ]
    tokens = list(lexer.tokenize_stream(iter(lines)))
    line_tokens = [t for t in tokens if t.type == TokenType.LINE]
    assert len(line_tokens) == 2
    assert line_tokens[0].metadata == "1'"
    assert line_tokens[1].metadata == "2''"


def test_lexer_rulings_and_dollar_syntax():
    lexer = ATFLexer()
    lines = [
        "&P100998 = Test Dollar\n",
        "@obverse\n",
        "$ rest broken\n",
        "$ blank space\n",
        "$ seal 1\n",
    ]
    tokens = list(lexer.tokenize_stream(iter(lines)))
    structure_tokens = [t for t in tokens if t.type == TokenType.STRUCTURE]
    assert len(structure_tokens) == 3


def test_lexer_all_surfaces():
    lexer = ATFLexer()
    lines = [
        "&P100997 = Test Surfaces\n",
        "@tablet\n",
        "@obverse\n",
        "@reverse\n",
        "@left\n",
        "@right\n",
        "@top\n",
        "@bottom\n",
        "@seal 1\n",
    ]
    tokens = list(lexer.tokenize_stream(iter(lines)))
    surfaces = [t.value for t in tokens if t.type == TokenType.SURFACE]
    assert "obverse" in surfaces
    assert "reverse" in surfaces
    assert "left" in surfaces
    objects = [t.value for t in tokens if t.type == TokenType.OBJECT_TYPE]
    assert any("tablet" in o for o in objects)
    assert any("seal" in o for o in objects)


# ---------------------------------------------------------------------------
# 2. Parser Edge Cases & Damaged Sign Preservations
# ---------------------------------------------------------------------------

def test_parser_sign_damage_flags():
    parser = ATFParser()
    raw = (
        "&P100996 = Damage Test\n"
        "@obverse\n"
        "1. udu# masz2? gu4! ba-zi\n"
    )
    tablets = parser.parse_string(raw)
    assert len(tablets) == 1
    signs = tablets[0].lines[0].signs
    assert len(signs) == 4

    # udu#
    assert signs[0].clean_value == "udu"
    assert signs[0].damage_flag == "#"

    # masz2?
    assert signs[1].clean_value == "masz2"
    assert signs[1].damage_flag == "?"

    # gu4!
    assert signs[2].clean_value == "gu4"
    assert signs[2].damage_flag == "!"


def test_parser_bracketed_restorations():
    parser = ATFParser()
    raw = (
        "&P100995 = Bracket Test\n"
        "@obverse\n"
        "1. [ki ab-ba]-sa6-ga-ta\n"
    )
    tablets = parser.parse_string(raw)
    line = tablets[0].lines[0]
    assert line.is_damaged is True
    assert any(s.is_broken for s in line.signs)


def test_parser_metrology_fractions():
    extractor = LedgerExtractor()
    assert extractor._parse_quantity("1/2(disz)") == 0.5
    assert extractor._parse_quantity("1/3(disz)") == pytest.approx(0.3333, abs=1e-3)
    assert extractor._parse_quantity("2/3(disz)") == pytest.approx(0.6666, abs=1e-3)
    assert extractor._parse_quantity("5/6(disz)") == pytest.approx(0.8333, abs=1e-3)


def test_parser_determinative_preservation():
    parser = ATFParser()
    raw = (
        "&P100994 = Det Test\n"
        "@obverse\n"
        "1. mu {d}amar-{d}suen lugal\n"
    )
    tablets = parser.parse_string(raw)
    line = tablets[0].lines[0]
    assert len(line.signs) >= 3
    assert line.signs[1].sign_type == "DETERMINATIVE" or "amar" in line.signs[1].clean_value


# ---------------------------------------------------------------------------
# 3. Ledger Extraction & Conservation Invariants
# ---------------------------------------------------------------------------

def test_ledger_double_entry_conservation_invariant():
    """Mathematical guarantee: for any closed transfer (ki X-ta Y i3-dab5), sum of deltas == 0."""
    parser = ATFParser()
    raw = (
        "&P100993 = Balance Invariant Test\n"
        "@obverse\n"
        "1. 10(disz) udu\n"
        "2. ki ab-ba-sa6-ga-ta\n"
        "3. in-ta-e3-a i3-dab5\n"
    )
    tablets = parser.parse_string(raw)
    extractor = LedgerExtractor()
    txs = extractor.extract_corpus(tablets)
    assert len(txs) == 1
    assert txs[0].source_party == "ab-ba-sa6-ga"
    assert txs[0].receiving_party == "in-ta-e3-a"

    auditor = LedgerAuditor()
    balances = auditor.compute_balances(txs)
    b_df = auditor.to_dataframe(balances)

    # Net sum of inventory deltas across source (-10) and receiver (+10) must be identically 0
    total_delta = b_df["net_inventory"].sum()
    assert total_delta == pytest.approx(0.0, abs=1e-6)


def test_ledger_disbursement_bazi_flow():
    """Expenditures (ba-zi) correctly debit disburser account without requiring a named receiver."""
    parser = ATFParser()
    raw = (
        "&P100992 = Bazi Test\n"
        "@obverse\n"
        "1. 5(disz) udu\n"
        "2. ki lu2-kal-la-ta\n"
        "3. ba-zi\n"
    )
    tablets = parser.parse_string(raw)
    extractor = LedgerExtractor()
    txs = extractor.extract_corpus(tablets)
    assert len(txs) == 1
    assert txs[0].action_type == "EXPENDITURE"
    assert txs[0].source_party == "lu2-kal-la"
    assert txs[0].quantity == 5.0


def test_ledger_multi_commodity_separation():
    """Different commodities (udu vs sze) are correctly separated on multiple lines."""
    parser = ATFParser()
    raw = (
        "&P100991 = Multi-Commodity Test\n"
        "@obverse\n"
        "1. 4(disz) udu\n"
        "2. 2(u) masz2\n"
        "3. ki ab-ba-sa6-ga-ta\n"
        "4. in-ta-e3-a i3-dab5\n"
    )
    tablets = parser.parse_string(raw)
    extractor = LedgerExtractor()
    txs = extractor.extract_corpus(tablets)
    assert len(txs) == 2
    commodities = {tx.commodity for tx in txs}
    assert "udu" in commodities
    assert "masz2" in commodities


# ---------------------------------------------------------------------------
# 4. K-mer Indexer Mathematical Properties
# ---------------------------------------------------------------------------

def test_kmer_jaccard_identity():
    """J(A, A) == 1.0 for non-empty sets."""
    indexer = KmerIndexer(k=4)
    s = {"abcd", "efgh", "ijkl"}
    assert indexer.jaccard_similarity(s, s) == 1.0


def test_kmer_jaccard_disjoint():
    """J(A, B) == 0.0 for completely disjoint sets."""
    indexer = KmerIndexer(k=4)
    s1 = {"aaaa", "bbbb"}
    s2 = {"cccc", "dddd"}
    assert indexer.jaccard_similarity(s1, s2) == 0.0


def test_kmer_jaccard_empty():
    """J(empty, empty) == 1.0, J(non-empty, empty) == 0.0."""
    indexer = KmerIndexer(k=4)
    assert indexer.jaccard_similarity(set(), set()) == 1.0
    assert indexer.jaccard_similarity({"aaaa"}, set()) == 0.0


def test_kmer_jaccard_symmetry():
    """J(A, B) == J(B, A)."""
    indexer = KmerIndexer(k=4)
    s1 = {"aaaa", "bbbb", "cccc"}
    s2 = {"bbbb", "cccc", "dddd"}
    assert indexer.jaccard_similarity(s1, s2) == indexer.jaccard_similarity(s2, s1)


def test_kmer_short_string_no_crash():
    """Extracting k-mers from a string shorter than k returns fallback without error."""
    indexer = KmerIndexer(k=4)
    kmers = indexer.extract_char_kmers("ab")
    assert "ab" in kmers


# ---------------------------------------------------------------------------
# 5. Chronos Solver & Prosopography
# ---------------------------------------------------------------------------

def test_chronos_intact_year_formula():
    """Intact year formula is recognized directly as CERTIFIED_DATED."""
    parser = ATFParser()
    raw = (
        "&P100990 = Dated Test\n"
        "@reverse\n"
        "1. iti ezem-an-na\n"
        "2. mu {d}amar-{d}suen lugal-e ur-bi2-lum{ki} mu-hul\n"
    )
    tablets = parser.parse_string(raw)
    solver = ChronosSolver()
    estimates = solver.fit_and_resolve(tablets)
    assert len(estimates) == 1
    assert estimates[0].status == "CERTIFIED_DATED"
    assert estimates[0].resolved_year == "AS02"


def test_chronos_unknown_official_graceful_handling():
    """Undated tablet with an unknown official falls back without raising an exception."""
    parser = ATFParser()
    raw = (
        "&P100989 = Unknown Actor Test\n"
        "@obverse\n"
        "1. 2(disz) udu\n"
        "2. ki non-existent-official-ta\n"
        "3. mysterious-person i3-dab5\n"
    )
    tablets = parser.parse_string(raw)
    solver = ChronosSolver()
    estimates = solver.fit_and_resolve(tablets)
    assert len(estimates) == 1
    assert estimates[0].status in {"UNDETERMINED", "ESTIMATED"}


# ---------------------------------------------------------------------------
# 6. Linter Edge Cases
# ---------------------------------------------------------------------------

def test_linter_unmatched_brackets_detected():
    auditor = BracketAuditor()
    issues = auditor.audit_line("P100000", "L1", "obverse", 1, "1. [1(disz) udu niga")
    assert any(i.rule_id == "B001" for i in issues)


def test_linter_unmatched_parentheses_detected():
    auditor = BracketAuditor()
    issues = auditor.audit_line("P100000", "L1", "obverse", 1, "1. 1(disz udu niga")
    assert any(i.rule_id == "B004" for i in issues)


def test_linter_clean_line_zero_issues():
    auditor = BracketAuditor()
    issues = auditor.audit_line("P100000", "L1", "obverse", 1, "1. 1(disz) udu niga")
    assert len(issues) == 0


# ---------------------------------------------------------------------------
# 7. File Sharder & SHA-256 Invariants
# ---------------------------------------------------------------------------

def test_file_sharder_roundtrip():
    """Verifies that sharding and reassembly preserves byte-exact SHA-256."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_db.bin")
        payload = b"Nisaba Cuneiform Engine Test Payload 12345\n" * 1000
        with open(test_file, "wb") as f:
            f.write(payload)

        sharder = FileSharder()
        orig_hash = sharder.compute_sha256(test_file)
        manifest = sharder.split_file(test_file, tmpdir, chunk_size_mb=1)
        assert manifest.expected_sha256 == orig_hash
        assert manifest.total_parts >= 1

        reconstituted = os.path.join(tmpdir, "reconstituted.bin")
        manifest_file = os.path.join(tmpdir, "test_db.bin.manifest.json")
        out_path = sharder.reassemble_file(manifest_file, reconstituted)
        assert os.path.exists(out_path)
        assert sharder.compute_sha256(reconstituted) == orig_hash


# ---------------------------------------------------------------------------
# 8. API & Taxonomy Invariants
# ---------------------------------------------------------------------------

def test_taxonomy_king_order_chronology():
    """Validates chronological order of Ur III royal codes."""
    codes = [yf.code for yf in YEAR_CATALOG]
    sh_indices = [i for i, c in enumerate(codes) if c.startswith("SH")]
    as_indices = [i for i, c in enumerate(codes) if c.startswith("AS")]
    ss_indices = [i for i, c in enumerate(codes) if c.startswith("SS")]
    is_indices = [i for i, c in enumerate(codes) if c.startswith("IS")]

    assert max(sh_indices) < min(as_indices), "Shulgi must precede Amar-Sin"
    assert max(as_indices) < min(ss_indices), "Amar-Sin must precede Shu-Sin"
    assert max(ss_indices) < min(is_indices), "Shu-Sin must precede Ibbi-Sin"


def test_api_404_on_unknown_tablet():
    client = TestClient(app)
    res = client.get("/api/tablets/P999999")
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data


def test_api_search_endpoint():
    client = TestClient(app)
    res = client.get("/api/search?q=udu&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id_text" in data[0]
