"""
Ur III Economic Balance Sheet and Inventory Auditor.
Aggregates inflows and disbursements per administrative officer.
"""

from dataclasses import dataclass
from typing import Dict, List
import pandas as pd

from src.ledger.extractor import TransactionRecord


@dataclass
class OfficerBalance:
    officer: str
    commodity: str
    total_received: float
    total_expended: float
    net_inventory: float


class LedgerAuditor:
    """Audits balanced double-entry accounting records across administrative officers."""

    def compute_balances(self, transactions: List[TransactionRecord]) -> List[OfficerBalance]:
        """Calculates aggregated debits, credits, and net balances per officer and commodity."""
        received_map: Dict[str, Dict[str, float]] = {}
        expended_map: Dict[str, Dict[str, float]] = {}

        for tx in transactions:
            comm = tx.commodity

            # Inflow to receiving party
            if tx.receiving_party and tx.receiving_party != "Unknown":
                rec = tx.receiving_party
                if rec not in received_map:
                    received_map[rec] = {}
                received_map[rec][comm] = received_map[rec].get(comm, 0.0) + tx.quantity

            # Outflow from source party
            if tx.source_party and tx.source_party != "Unknown":
                src = tx.source_party
                if src not in expended_map:
                    expended_map[src] = {}
                expended_map[src][comm] = expended_map[src].get(comm, 0.0) + tx.quantity

        all_officers = set(received_map.keys()) | set(expended_map.keys())
        balances: List[OfficerBalance] = []

        for off in sorted(list(all_officers)):
            commodities = set(received_map.get(off, {}).keys()) | set(expended_map.get(off, {}).keys())
            for c in sorted(list(commodities)):
                inflow = received_map.get(off, {}).get(c, 0.0)
                outflow = expended_map.get(off, {}).get(c, 0.0)
                balances.append(OfficerBalance(
                    officer=off,
                    commodity=c,
                    total_received=inflow,
                    total_expended=outflow,
                    net_inventory=inflow - outflow,
                ))

        return balances

    def to_dataframe(self, balances: List[OfficerBalance]) -> pd.DataFrame:
        """Converts officer balances to a DataFrame."""
        return pd.DataFrame([
            {
                "officer": b.officer,
                "commodity": b.commodity,
                "total_received": b.total_received,
                "total_expended": b.total_expended,
                "net_inventory": b.net_inventory,
            }
            for b in balances
        ])
