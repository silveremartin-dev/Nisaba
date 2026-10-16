"""
Ur III Economic Transaction Extractor.
Extracts structured double-entry financial events from formulaic Sumerian administrative texts.
"""

from dataclasses import dataclass
import re
from typing import List, Optional
import pandas as pd

from src.compiler.parser import TabletRecord
from src.chronos.prosopography import ProsopographyExtractor


@dataclass
class TransactionRecord:
    id_text: str
    id_line: str
    quantity: float
    commodity: str
    source_party: Optional[str]        # Debited party (ki ... -ta)
    receiving_party: Optional[str]     # Credited party (i3-dab5 / kiszib3)
    action_type: str                   # RECEIPT (i3-dab5), DISBURSEMENT (ba-zi), RECORD
    month: Optional[str]
    year: Optional[str]


class LedgerExtractor:
    """Extracts accounting transaction records from parsed tablets."""

    RE_NUM_COMMODITY = re.compile(
        r"^(\d+)\((?:disz|asz|u|gesz2)?\)\s+([a-z0-9_\-\{\}\s]+?)(?:\s+ba-usz2|\s+u4|\s+ki|\s+$)",
        re.IGNORECASE
    )

    def __init__(self):
        self.proso = ProsopographyExtractor()

    def _parse_quantity(self, token: str) -> float:
        """Parses cuneiform numerical token to decimal value."""
        m = re.match(r"^(\d+)\(([a-z0-9\']+)\)", token)
        if not m:
            return 1.0
        val = float(m.group(1))
        unit = m.group(2).lower()
        if unit == "u":
            return val * 10.0
        if unit == "gesz2":
            return val * 60.0
        return val

    def extract_transactions(self, tablet: TabletRecord) -> List[TransactionRecord]:
        """Extracts all economic entries from a tablet."""
        entities = self.proso.extract_from_tablet(tablet)

        # Identify primary source and receiver for the tablet
        source_party = None
        receiving_party = None
        action_type = "RECORD"

        for line in tablet.lines:
            raw = line.raw_text
            m_ki = re.search(r"ki\s+([a-z0-9_\-\{\}]+)\-ta", raw)
            if m_ki:
                source_party = re.sub(r"[\[\]#\?!]", "", m_ki.group(1)).strip()

            m_dab = re.search(r"([a-z0-9_\-\{\}]+)\s+i3-dab5", raw)
            if m_dab:
                receiving_party = re.sub(r"[\[\]#\?!]", "", m_dab.group(1)).strip()
                action_type = "INWARD_TRANSFER"

            m_kisz = re.search(r"kiszib3\s+([a-z0-9_\-\{\}]+)", raw)
            if m_kisz and not receiving_party:
                receiving_party = re.sub(r"[\[\]#\?!]", "", m_kisz.group(1)).strip()
                action_type = "SEALED_RECEIPT"

            if "ba-zi" in raw:
                action_type = "EXPENDITURE"

        transactions: List[TransactionRecord] = []

        # Find commodity quantities on lines
        for line in tablet.lines:
            tokens = line.normalized_text.split()
            if not tokens:
                continue

            # Look for number at start of line
            if re.match(r"^\d+\([a-z0-9\']+\)", tokens[0]):
                qty = self._parse_quantity(tokens[0])
                # Remainder of line up to transaction verbs is the commodity
                commodity_tokens = []
                for tok in tokens[1:]:
                    if tok in ("ba-usz2", "ki", "i3-dab5", "ba-zi", "kiszib3", "u4", "iti", "mu"):
                        break
                    commodity_tokens.append(tok)

                commodity = " ".join(commodity_tokens).strip() or "general_goods"

                transactions.append(TransactionRecord(
                    id_text=tablet.id_text,
                    id_line=line.id_line,
                    quantity=qty,
                    commodity=commodity,
                    source_party=source_party,
                    receiving_party=receiving_party,
                    action_type=action_type,
                    month=entities.month_name,
                    year=entities.year_code,
                ))

        return transactions

    def extract_corpus(self, tablets: List[TabletRecord]) -> List[TransactionRecord]:
        """Extracts transactions across the entire corpus."""
        all_tx: List[TransactionRecord] = []
        for tab in tablets:
            all_tx.extend(self.extract_transactions(tab))
        return all_tx

    def to_dataframe(self, transactions: List[TransactionRecord]) -> pd.DataFrame:
        """Converts transactions list to DataFrame."""
        return pd.DataFrame([
            {
                "id_text": tx.id_text,
                "id_line": tx.id_line,
                "quantity": tx.quantity,
                "commodity": tx.commodity,
                "source_party": tx.source_party or "Unknown",
                "receiving_party": tx.receiving_party or "Unknown",
                "action_type": tx.action_type,
                "month": tx.month or "Unknown",
                "year": tx.year or "Undated",
            }
            for tx in transactions
        ])
