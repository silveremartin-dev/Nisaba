"""
Prosopographic entity extractor and co-occurrence graph builder for Ur III tablets.
"""

from dataclasses import dataclass, field
import re
from typing import Dict, List, Set
import networkx as nx

from src.compiler.parser import TabletRecord
from src.chronos.year_names import YearNormalizer


@dataclass
class TabletEntities:
    id_text: str
    year_code: Optional[str]  # e.g. "AS02", None if undated
    month_name: Optional[str]
    officials: List[str] = field(default_factory=list)
    seal_legends: List[str] = field(default_factory=list)


class ProsopographyExtractor:
    """Extracts officials, scribes, seals, and temporal markers from tablet lines."""

    RE_KI_TA = re.compile(r"ki\s+([a-z0-9_\-\{\}]+)\-ta", re.IGNORECASE)
    RE_I3_DAB5 = re.compile(r"([a-z0-9_\-\{\}]+)\s+i3-dab5", re.IGNORECASE)
    RE_KISZIB3 = re.compile(r"kiszib3\s+([a-z0-9_\-\{\}]+)", re.IGNORECASE)
    RE_ITI = re.compile(r"(iti\s+[a-z0-9_\-\{\}]+(?:\-[a-z0-9_\-\{\}]+)?)", re.IGNORECASE)

    def __init__(self):
        self.year_normalizer = YearNormalizer()

    def extract_from_tablet(self, tablet: TabletRecord) -> TabletEntities:
        """Extracts actors, seals, and dates from a single tablet."""
        officials: Set[str] = set()
        month_name: Optional[str] = None
        year_code: Optional[str] = None
        seals: List[str] = []

        for line in tablet.lines:
            raw = line.raw_text

            # Check year name
            if raw.startswith("mu ") or raw.startswith("mu-"):
                yf = self.year_normalizer.normalize(raw)
                if yf:
                    year_code = yf.code

            # Check month
            m_iti = self.RE_ITI.search(raw)
            if m_iti and not month_name:
                month_name = m_iti.group(1).lower().strip()

            # Check source official ki ... -ta
            m_kita = self.RE_KI_TA.search(raw)
            if m_kita:
                clean_name = re.sub(r"[\[\]#\?!]", "", m_kita.group(1)).strip()
                if clean_name not in ("...", "x", "X"):
                    officials.add(clean_name)

            # Check receiving official ... i3-dab5
            m_dab = self.RE_I3_DAB5.search(raw)
            if m_dab:
                clean_name = re.sub(r"[\[\]#\?!]", "", m_dab.group(1)).strip()
                if clean_name not in ("...", "x", "X"):
                    officials.add(clean_name)

            # Check seal receipt kiszib3 ...
            m_kisz = self.RE_KISZIB3.search(raw)
            if m_kisz:
                clean_name = re.sub(r"[\[\]#\?!]", "", m_kisz.group(1)).strip()
                if clean_name not in ("...", "x", "X"):
                    officials.add(clean_name)

            # Check seal section
            if "seal" in line.surface:
                seals.append(line.normalized_text)

        return TabletEntities(
            id_text=tablet.id_text,
            year_code=year_code,
            month_name=month_name,
            officials=sorted(list(officials)),
            seal_legends=seals,
        )

    def build_activity_index(self, tablets: List[TabletRecord]) -> Dict[str, Set[str]]:
        """Maps each official/entity to the set of dated year codes where they appear."""
        index: Dict[str, Set[str]] = {}
        for tab in tablets:
            entities = self.extract_from_tablet(tab)
            if entities.year_code:
                for off in entities.officials:
                    if off not in index:
                        index[off] = set()
                    index[off].add(entities.year_code)
        return index
