"""
k-mer indexer and similarity metrics for Sumerian cuneiform transliteration lines.
"""

from typing import List, Set


class KmerIndexer:
    """Extracts character and token k-mers from transliterated cuneiform strings."""

    def __init__(self, k: int = 4):
        self.k = k

    def extract_char_kmers(self, text: str) -> Set[str]:
        """Extracts sliding character k-mers from text."""
        clean = "".join(c for c in text.lower() if c.isalnum() or c in ("-", "_"))
        if len(clean) < self.k:
            return {clean} if clean else set()
        return {clean[i:i + self.k] for i in range(len(clean) - self.k + 1)}

    def extract_token_kmers(self, text: str, token_k: int = 2) -> Set[str]:
        """Extracts n-grams of words/signs."""
        tokens = text.strip().split()
        if len(tokens) < token_k:
            return {" ".join(tokens)} if tokens else set()
        return {" ".join(tokens[i:i + token_k]) for i in range(len(tokens) - token_k + 1)}

    def jaccard_similarity(self, set_a: Set[str], set_b: Set[str]) -> float:
        """Calculates standard Jaccard set similarity."""
        if not set_a and not set_b:
            return 1.0
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0
