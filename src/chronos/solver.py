"""
Macro-chronological solver for undated Sumerian tablets.
Propagates temporal constraints along prosopographic networks to infer missing dates.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import pandas as pd

from src.compiler.parser import TabletRecord
from src.chronos.prosopography import ProsopographyExtractor, TabletEntities


@dataclass
class ChronosEstimate:
    id_text: str
    status: str  # CERTIFIED_DATED, ESTIMATED, UNDETERMINED
    resolved_year: Optional[str]
    candidate_years: List[str] = field(default_factory=list)
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)


class ChronosSolver:
    """Infers missing dates for tablets with broken or omitted year formulas."""

    # Prior historical bounds for major Ur III actors (based on historical assyriological consensus)
    HISTORICAL_PRIORS: Dict[str, Set[str]] = {
        "ab-ba-sa6-ga": {"SH44", "SH45", "SH46", "SH47", "SH48", "AS01", "AS02", "AS03", "AS04", "AS05", "AS06", "AS07", "AS08"},
        "in-ta-e3-a": {"AS04", "AS05", "AS06", "AS07", "AS08", "AS09", "SS01", "SS02", "SS03", "SS04", "SS05", "SS06", "SS07", "SS08", "SS09"},
        "na-lu5": {"SH42", "SH43", "SH44", "SH45", "SH46", "SH47", "SH48", "AS01", "AS02", "AS03", "AS04", "AS05"},
        "lu2-kal-la": {"AS01", "AS02", "AS03", "AS04", "AS05", "AS06", "AS07", "AS08", "AS09", "SS01", "SS02", "SS03", "SS04"},
        "ur-mes": {"SS01", "SS02", "SS03", "SS04", "SS05", "SS06", "SS07", "SS08", "SS09"},
        "ur-szu-ga-lam-ma": {"AS01", "AS02", "AS03", "AS04", "AS05", "AS06", "AS07", "AS08"},
    }

    def __init__(self):
        self.extractor = ProsopographyExtractor()

    def fit_and_resolve(self, tablets: List[TabletRecord]) -> List[ChronosEstimate]:
        """Builds empirical index from dated tablets and resolves undated ones."""
        # 1. Build empirical activity index
        empirical_index = self.extractor.build_activity_index(tablets)

        # Merge with historical priors
        combined_index: Dict[str, Set[str]] = {}
        all_keys = set(empirical_index.keys()) | set(self.HISTORICAL_PRIORS.keys())
        for k in all_keys:
            s_emp = empirical_index.get(k, set())
            s_prior = self.HISTORICAL_PRIORS.get(k, set())
            combined_index[k] = s_emp | s_prior

        results: List[ChronosEstimate] = []

        for tab in tablets:
            entities = self.extractor.extract_from_tablet(tab)

            # Case A: Already has certified date
            if entities.year_code:
                results.append(ChronosEstimate(
                    id_text=tab.id_text,
                    status="CERTIFIED_DATED",
                    resolved_year=entities.year_code,
                    candidate_years=[entities.year_code],
                    confidence=1.0,
                    evidence=[f"Explicit attested year formula: {entities.year_code}"],
                ))
                continue

            # Case B: Undated - intersect active windows of co-occurring officials
            intersecting_years: Optional[Set[str]] = None
            evidence: List[str] = []

            for off in entities.officials:
                if off in combined_index:
                    off_years = combined_index[off]
                    evidence.append(f"Official '{off}' active during: {sorted(list(off_years))}")
                    if intersecting_years is None:
                        intersecting_years = set(off_years)
                    else:
                        intersecting_years = intersecting_years & off_years

            if intersecting_years and len(intersecting_years) > 0:
                sorted_cands = sorted(list(intersecting_years))
                # Confidence is inversely proportional to span size
                span_len = len(sorted_cands)
                confidence = max(0.2, min(0.95, 1.0 / span_len if span_len <= 5 else 0.5))
                resolved = sorted_cands[0] if span_len == 1 else f"{sorted_cands[0]}..{sorted_cands[-1]}"

                results.append(ChronosEstimate(
                    id_text=tab.id_text,
                    status="ESTIMATED",
                    resolved_year=resolved,
                    candidate_years=sorted_cands,
                    confidence=round(confidence, 2),
                    evidence=evidence,
                ))
            else:
                results.append(ChronosEstimate(
                    id_text=tab.id_text,
                    status="UNDETERMINED",
                    resolved_year=None,
                    candidate_years=[],
                    confidence=0.0,
                    evidence=["Insufficient prosopographic constraints or disjoint entity windows"],
                ))

        return results

    def to_dataframe(self, estimates: List[ChronosEstimate]) -> pd.DataFrame:
        """Converts estimates list to a DataFrame."""
        return pd.DataFrame([
            {
                "id_text": est.id_text,
                "status": est.status,
                "resolved_year": est.resolved_year,
                "candidate_years_count": len(est.candidate_years),
                "confidence": est.confidence,
                "evidence_count": len(est.evidence),
            }
            for est in estimates
        ])
