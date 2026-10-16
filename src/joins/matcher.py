"""
Fragment Joiner and Virtual Match Finder for dispersed cuneiform tablets.
Detects potential physical fragment joins and duplicate administrative series.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
import pandas as pd

from src.compiler.parser import TabletRecord
from src.joins.kmer import KmerIndexer


@dataclass
class JoinCandidate:
    id_text_a: str
    id_text_b: str
    join_type: str  # VIRTUAL_JOIN_CANDIDATE, DUPLICATE_ADMIN_SERIES
    similarity_score: float
    matched_lines_count: int
    complementary_breaks: bool
    evidence_sample: List[str] = field(default_factory=list)


class FragmentMatcher:
    """Discovers prospective text joins across international tablet collections."""

    def __init__(self, k: int = 4, min_similarity: float = 0.35):
        self.indexer = KmerIndexer(k=k)
        self.min_similarity = min_similarity

    def find_joins(self, tablets: List[TabletRecord]) -> List[JoinCandidate]:
        """Performs all-against-all comparison across tablets in the corpus."""
        candidates: List[JoinCandidate] = []
        n = len(tablets)

        # Pre-compute k-mer sets per tablet
        tablet_kmers: Dict[str, Set[str]] = {}
        tablet_has_breaks: Dict[str, bool] = {}

        for tab in tablets:
            all_text = " ".join(line.normalized_text for line in tab.lines)
            tablet_kmers[tab.id_text] = self.indexer.extract_char_kmers(all_text)
            tablet_has_breaks[tab.id_text] = any(line.is_damaged for line in tab.lines)

        for i in range(n):
            for j in range(i + 1, n):
                t_a = tablets[i]
                t_b = tablets[j]

                kmers_a = tablet_kmers[t_a.id_text]
                kmers_b = tablet_kmers[t_b.id_text]

                sim = self.indexer.jaccard_similarity(kmers_a, kmers_b)

                if sim >= self.min_similarity:
                    both_broken = tablet_has_breaks[t_a.id_text] and tablet_has_breaks[t_b.id_text]
                    join_type = "VIRTUAL_JOIN_CANDIDATE" if both_broken else "DUPLICATE_ADMIN_SERIES"

                    # Find matched line samples
                    evidence = []
                    matched_lines = 0
                    for l_a in t_a.lines:
                        km_la = self.indexer.extract_char_kmers(l_a.normalized_text)
                        for l_b in t_b.lines:
                            km_lb = self.indexer.extract_char_kmers(l_b.normalized_text)
                            if self.indexer.jaccard_similarity(km_la, km_lb) > 0.6:
                                matched_lines += 1
                                if len(evidence) < 3:
                                    evidence.append(f"A: '{l_a.raw_text}' <-> B: '{l_b.raw_text}'")

                    candidates.append(JoinCandidate(
                        id_text_a=t_a.id_text,
                        id_text_b=t_b.id_text,
                        join_type=join_type,
                        similarity_score=round(sim, 3),
                        matched_lines_count=matched_lines,
                        complementary_breaks=both_broken,
                        evidence_sample=evidence,
                    ))

        # Sort descending by similarity score
        candidates.sort(key=lambda c: c.similarity_score, reverse=True)
        return candidates

    def to_dataframe(self, candidates: List[JoinCandidate]) -> pd.DataFrame:
        """Converts candidates list to a DataFrame."""
        return pd.DataFrame([
            {
                "id_text_a": c.id_text_a,
                "id_text_b": c.id_text_b,
                "join_type": c.join_type,
                "similarity_score": c.similarity_score,
                "matched_lines_count": c.matched_lines_count,
                "complementary_breaks": c.complementary_breaks,
            }
            for c in candidates
        ])
