"""
Scribe and Author Identification Engine for Sumerian Cuneiform Tablets.
Identifies ancient scribes via explicit seal legends, colophons (dub-sar), and patronymics,
and performs stylistic/prosopographic fingerprinting to attribute anonymous tablets.
"""

from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional, Set
import pandas as pd

from src.compiler.parser import TabletRecord


@dataclass
class ScribeProfile:
    scribe_name: str
    title: str = "dub-sar"  # scribe
    father_name: Optional[str] = None
    attested_years: Set[str] = field(default_factory=set)
    seal_legends: List[str] = field(default_factory=list)
    tablet_count: int = 0


@dataclass
class AttributionResult:
    id_text: str
    attribution_type: str  # EXPLICIT_SEAL, EXPLICIT_COLOPHON, PROBABILISTIC_STYLE, UNKNOWN
    identified_scribe: Optional[str]
    patronymic: Optional[str]
    title: Optional[str]
    confidence: float
    evidence: List[str] = field(default_factory=list)


class AuthorIdentifier:
    """Discovers and attributes tablet scribes and authors."""

    RE_DUBSAR = re.compile(r"([a-z0-9_\-\{\}]+)\s+dub-sar", re.IGNORECASE)
    RE_GIRI3 = re.compile(r"giri3\s+([a-z0-9_\-\{\}]+)(?:\s+dub-sar)?", re.IGNORECASE)
    RE_DUMU = re.compile(r"dumu\s+([a-z0-9_\-\{\}]+)", re.IGNORECASE)
    RE_KISZIB3 = re.compile(r"kiszib3\s+([a-z0-9_\-\{\}]+)", re.IGNORECASE)

    # Historical canonical scribes of Ur III chancelleries
    CANONICAL_SCRIBES: Dict[str, Dict[str, str]] = {
        "lu2-kal-la": {"title": "dub-sar", "father": "ur-e11-e", "provenance": "Umma"},
        "ur-mes": {"title": "dub-sar", "father": "la-na-ab", "provenance": "Puzrish-Dagan"},
        "ur-szu-ga-lam-ma": {"title": "dub-sar", "father": "ur-sa6-ga", "provenance": "Puzrish-Dagan"},
        "lugal-iti-da": {"title": "dub-sar", "father": "ur-{d}dumu-zi", "provenance": "Umma"},
        "in-ta-e3-a": {"title": "dub-sar", "father": "lu2-du10-ga", "provenance": "Puzrish-Dagan"},
    }

    def extract_explicit_author(self, tablet: TabletRecord) -> Optional[AttributionResult]:
        """Extracts author from seal inscriptions or explicit colophon lines."""
        # 1. Search Seal sections (@seal 1, @seal 2)
        seal_lines = [l.normalized_text for l in tablet.lines if "seal" in l.surface]
        if seal_lines:
            scribe_name = None
            title = "dub-sar"
            father_name = None

            for s_line in seal_lines:
                if "dub-sar" in s_line:
                    title = "dub-sar"
                m_dumu = self.RE_DUMU.search(s_line)
                if m_dumu:
                    father_name = m_dumu.group(1).strip()
                elif not scribe_name and s_line not in ("dub-sar", "szusz3"):
                    # First line of seal is usually the owner's name
                    tokens = s_line.split()
                    if tokens:
                        scribe_name = tokens[0].strip()

            if scribe_name:
                evidence = [f"Found in seal inscription: '{' / '.join(seal_lines)}'"]
                return AttributionResult(
                    id_text=tablet.id_text,
                    attribution_type="EXPLICIT_SEAL",
                    identified_scribe=scribe_name,
                    patronymic=father_name,
                    title=title,
                    confidence=1.0,
                    evidence=evidence,
                )

        # 2. Search for explicit colophon: 'giri3 <NAME> dub-sar' or 'kiszib3 <NAME>'
        for line in tablet.lines:
            raw = line.raw_text
            m_giri = self.RE_GIRI3.search(raw)
            if m_giri and "dub-sar" in raw:
                name = m_giri.group(1).strip()
                return AttributionResult(
                    id_text=tablet.id_text,
                    attribution_type="EXPLICIT_COLOPHON",
                    identified_scribe=name,
                    patronymic=self.CANONICAL_SCRIBES.get(name, {}).get("father"),
                    title="dub-sar",
                    confidence=0.95,
                    evidence=[f"Conveying scribe colophon: '{line.raw_text}'"],
                )

            m_kisz = self.RE_KISZIB3.search(raw)
            if m_kisz:
                name = m_kisz.group(1).strip()
                if name in self.CANONICAL_SCRIBES:
                    info = self.CANONICAL_SCRIBES[name]
                    return AttributionResult(
                        id_text=tablet.id_text,
                        attribution_type="EXPLICIT_RECEIVER_SEAL",
                        identified_scribe=name,
                        patronymic=info.get("father"),
                        title=info.get("title", "dub-sar"),
                        confidence=0.90,
                        evidence=[f"Attested administrative certifying official: '{name}'"],
                    )

        return None

    def attribute_tablet(self, tablet: TabletRecord, corpus_tablets: Optional[List[TabletRecord]] = None) -> AttributionResult:
        """Attributes tablet to an author via seal, colophon, or network affinity."""
        explicit = self.extract_explicit_author(tablet)
        if explicit:
            return explicit

        # Probabilistic fingerprinting based on lexical and recipient overlap
        scores: Dict[str, float] = {}
        for line in tablet.lines:
            # High priority: receiving official who took custody and recorded the transaction
            m_dab = re.search(r"([a-z0-9_\-\{\}]+)\s+i3-dab5", line.raw_text, re.IGNORECASE)
            if m_dab:
                dab_name = m_dab.group(1).strip()
                if dab_name in self.CANONICAL_SCRIBES:
                    scores[dab_name] = scores.get(dab_name, 0.0) + 4.0

            for scribe, info in self.CANONICAL_SCRIBES.items():
                if scribe in line.normalized_text:
                    scores[scribe] = scores.get(scribe, 0.0) + 1.0
                father = info.get("father")
                if father and father in line.normalized_text:
                    scores[scribe] = scores.get(scribe, 0.0) + 1.5

        if scores:
            best_scribe = max(scores.keys(), key=lambda k: scores[k])
            info = self.CANONICAL_SCRIBES[best_scribe]
            return AttributionResult(
                id_text=tablet.id_text,
                attribution_type="PROBABILISTIC_STYLE",
                identified_scribe=best_scribe,
                patronymic=info.get("father"),
                title=info.get("title", "dub-sar"),
                confidence=0.75,
                evidence=[f"Prosopographic co-occurrence score: {scores[best_scribe]}"],
            )

        return AttributionResult(
            id_text=tablet.id_text,
            attribution_type="UNKNOWN",
            identified_scribe=None,
            patronymic=None,
            title=None,
            confidence=0.0,
            evidence=["No seal, colophon, or known scribal network signatures detected"],
        )

    def attribute_corpus(self, tablets: List[TabletRecord]) -> List[AttributionResult]:
        """Attributes all tablets across the corpus."""
        return [self.attribute_tablet(tab, tablets) for tab in tablets]

    def to_dataframe(self, results: List[AttributionResult]) -> pd.DataFrame:
        """Converts attributions to a DataFrame."""
        return pd.DataFrame([
            {
                "id_text": r.id_text,
                "attribution_type": r.attribution_type,
                "identified_scribe": r.identified_scribe or "Unknown",
                "patronymic": r.patronymic or "Unknown",
                "title": r.title or "Unknown",
                "confidence": r.confidence,
            }
            for r in results
        ])
