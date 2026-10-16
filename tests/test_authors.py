"""Tests for Scribe and Author Identification (AuthorIdentifier)."""

import pytest
from src.compiler.parser import ATFParser
from src.authors.scribe_identifier import AuthorIdentifier, AttributionResult


def test_author_explicit_seal_extraction():
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    # P100001 has seal 1:
    # 1. lu2-kal-la
    # 2. dub-sar
    # 3. dumu ur-e11-e szusz3
    t1 = next(t for t in tablets if t.id_text == "P100001")
    identifier = AuthorIdentifier()
    attr = identifier.attribute_tablet(t1)

    assert attr.attribution_type == "EXPLICIT_SEAL"
    assert attr.identified_scribe == "lu2-kal-la"
    assert attr.patronymic == "ur-e11-e"
    assert attr.title == "dub-sar"
    assert attr.confidence == 1.0


def test_author_probabilistic_attribution():
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    # P100003 mentions ur-mes
    t3 = next(t for t in tablets if t.id_text == "P100003")
    identifier = AuthorIdentifier()
    attr = identifier.attribute_tablet(t3)

    assert attr.identified_scribe == "ur-mes"
    assert attr.confidence >= 0.75


def test_author_corpus_batch():
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    identifier = AuthorIdentifier()
    results = identifier.attribute_corpus(tablets)

    assert len(results) == len(tablets)
    df = identifier.to_dataframe(results)
    assert len(df) == 7
    assert "identified_scribe" in df.columns
    assert "confidence" in df.columns
