"""Tests for KmerIndexer and FragmentMatcher."""

import pytest
from src.compiler.parser import ATFParser
from src.joins.kmer import KmerIndexer
from src.joins.matcher import FragmentMatcher


def test_kmer_indexer():
    indexer = KmerIndexer(k=4)
    kmers = indexer.extract_char_kmers("1(disz) udu niga")
    assert len(kmers) > 0

    # Jaccard
    s1 = {"abcd", "efgh"}
    s2 = {"abcd", "zzzz"}
    sim = indexer.jaccard_similarity(s1, s2)
    assert 0.3 < sim < 0.4


def test_fragment_matcher():
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    matcher = FragmentMatcher(min_similarity=0.25)
    joins = matcher.find_joins(tablets)

    assert isinstance(joins, list)
    # P100001 and P100007 are highly similar (ba-usz2 u4 2(u) 8(disz)-kam, ki ur-ru-ta, kiszib3 lu2-kal-la)
    match = next((j for j in joins if (j.id_text_a == "P100001" and j.id_text_b == "P100007") or (j.id_text_a == "P100007" and j.id_text_b == "P100001")), None)
    assert match is not None
    assert match.similarity_score > 0.4
    assert match.matched_lines_count >= 2
