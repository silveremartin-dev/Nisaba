"""
Data access and business logic service layer for Nisaba REST API.
Executes high-speed queries on DuckDB and cached Parquet tables.
"""

import os
from typing import Any, Dict, List, Optional
import duckdb
import pandas as pd


class NisabaDataService:
    """Provides querying capabilities over Nisaba DuckDB tables and analytical Parquet outputs."""

    def __init__(self, db_path: str = "data/processed/nisaba.duckdb", processed_dir: str = "data/processed"):
        self.db_path = db_path
        self.processed_dir = processed_dir

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Returns a read-only DuckDB connection."""
        if os.path.exists(self.db_path):
            return duckdb.connect(self.db_path, read_only=True)
        return duckdb.connect()

    def get_stats(self) -> Dict[str, Any]:
        """Returns macro statistics on the indexed cuneiform corpus."""
        con = self._get_connection()
        try:
            tablets_count = 0
            lines_count = 0
            signs_count = 0
            kmers_count = 0

            tables = [r[0] for r in con.execute("SHOW TABLES;").fetchall()]
            if "tablets" in tables:
                tablets_count = con.execute("SELECT COUNT(*) FROM tablets").fetchone()[0]
            if "lines" in tables:
                lines_count = con.execute("SELECT COUNT(*) FROM lines").fetchone()[0]
            if "signs" in tables:
                signs_count = con.execute("SELECT COUNT(*) FROM signs").fetchone()[0]
            if "kmers" in tables:
                kmers_count = con.execute("SELECT COUNT(*) FROM kmers").fetchone()[0]

            # Additional parquet tables if present
            authors_path = os.path.join(self.processed_dir, "author_attributions.parquet")
            authors_count = 0
            if os.path.exists(authors_path):
                p_norm = authors_path.replace("\\", "/")
                authors_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{p_norm}') WHERE identified_scribe IS NOT NULL").fetchone()[0]

            tx_path = os.path.join(self.processed_dir, "transactions.parquet")
            tx_count = 0
            if os.path.exists(tx_path):
                p_norm = tx_path.replace("\\", "/")
                tx_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{p_norm}')").fetchone()[0]

            joins_path = os.path.join(self.processed_dir, "virtual_joins.parquet")
            joins_count = 0
            if os.path.exists(joins_path):
                p_norm = joins_path.replace("\\", "/")
                joins_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{p_norm}')").fetchone()[0]

            return {
                "total_tablets": tablets_count,
                "total_lines": lines_count,
                "total_signs": signs_count,
                "total_kmers": kmers_count,
                "identified_scribes": authors_count,
                "audited_transactions": tx_count,
                "candidate_joins": joins_count,
                "engine_status": "ONLINE",
            }
        finally:
            con.close()

    def list_tablets(
        self,
        limit: int = 50,
        offset: int = 0,
        period: Optional[str] = None,
        provenance: Optional[str] = None,
        has_date: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Lists tablets with pagination and optional filters."""
        con = self._get_connection()
        try:
            where_clauses = []
            params = []
            if period:
                where_clauses.append("period = ?")
                params.append(period)
            if provenance:
                where_clauses.append("provenance = ?")
                params.append(provenance)
            if has_date is not None:
                where_clauses.append("has_date = ?")
                params.append(has_date)
            if search:
                where_clauses.append("(id_text ILIKE ? OR designation ILIKE ?)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            total = con.execute(f"SELECT COUNT(*) FROM tablets {where_str}", params).fetchone()[0]
            query = f"SELECT * FROM tablets {where_str} ORDER BY id_text LIMIT ? OFFSET ?"
            query_params = list(params) + [limit, offset]
            df = con.execute(query, query_params).df()

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "items": df.to_dict(orient="records"),
            }
        finally:
            con.close()

    def get_tablet_detail(self, id_text: str) -> Optional[Dict[str, Any]]:
        """Retrieves comprehensive tablet details: metadata, lines, signs, attribution, dates, and images."""
        con = self._get_connection()
        try:
            res_tab = con.execute("SELECT * FROM tablets WHERE id_text = ?", [id_text]).df()
            if res_tab.empty:
                return None
            tablet = res_tab.iloc[0].to_dict()

            # Lines
            df_lines = con.execute(
                "SELECT id_line, surface, line_number, line_label, raw_text, normalized_text, is_damaged, sign_count "
                "FROM lines WHERE id_text = ? ORDER BY line_number",
                [id_text]
            ).df()
            tablet["lines"] = df_lines.to_dict(orient="records")

            # Author attribution
            authors_path = os.path.join(self.processed_dir, "author_attributions.parquet")
            tablet["attribution"] = None
            if os.path.exists(authors_path):
                p_norm = authors_path.replace("\\", "/")
                df_auth = con.execute(f"SELECT * FROM read_parquet('{p_norm}') WHERE id_text = ?", [id_text]).df()
                if not df_auth.empty:
                    tablet["attribution"] = df_auth.iloc[0].to_dict()

            # Chronos estimate
            chronos_path = os.path.join(self.processed_dir, "chronos_estimates.parquet")
            tablet["chronos_estimate"] = None
            if os.path.exists(chronos_path):
                p_norm = chronos_path.replace("\\", "/")
                df_chron = con.execute(f"SELECT * FROM read_parquet('{p_norm}') WHERE id_text = ?", [id_text]).df()
                if not df_chron.empty:
                    tablet["chronos_estimate"] = df_chron.iloc[0].to_dict()

            # Virtual joins
            joins_path = os.path.join(self.processed_dir, "virtual_joins.parquet")
            tablet["candidate_joins"] = []
            if os.path.exists(joins_path):
                p_norm = joins_path.replace("\\", "/")
                df_joins = con.execute(
                    f"SELECT * FROM read_parquet('{p_norm}') WHERE id_text_a = ? OR id_text_b = ?",
                    [id_text, id_text]
                ).df()
                tablet["candidate_joins"] = df_joins.to_dict(orient="records")

            # Photos
            p_clean = id_text.strip().upper()
            tablet["photos"] = {
                "cdli_page": f"https://cdli.mpiwg-berlin.mpg.de/artifacts/{p_clean[1:] if p_clean.startswith('P') else p_clean}",
                "cdli_image_url": f"https://cdli.mpiwg-berlin.mpg.de/dl/photo/{p_clean}.jpg",
            }

            return tablet
        finally:
            con.close()

    def search_corpus(self, q: str, mode: str = "text", limit: int = 50) -> List[Dict[str, Any]]:
        """Performs full-text or sign search across the corpus lines."""
        con = self._get_connection()
        try:
            q_clean = q.strip()
            if mode == "kmer":
                query = """
                    SELECT k.id_text, k.id_line, l.line_number, l.raw_text, l.normalized_text
                    FROM kmers k
                    JOIN lines l ON k.id_line = l.id_line
                    WHERE k.kmer = ?
                    LIMIT ?
                """
                return con.execute(query, [q_clean, limit]).df().to_dict(orient="records")
            else:
                pattern = f"%{q_clean}%"
                query = """
                    SELECT id_text, id_line, line_number, surface, raw_text, normalized_text
                    FROM lines
                    WHERE raw_text ILIKE ? OR normalized_text ILIKE ?
                    ORDER BY id_text, line_number
                    LIMIT ?
                """
                return con.execute(query, [pattern, pattern, limit]).df().to_dict(orient="records")
        finally:
            con.close()

    def list_officials(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns audited officer balance sheets from ledger records."""
        balances_path = os.path.join(self.processed_dir, "officer_balances.parquet")
        if not os.path.exists(balances_path):
            return []

        con = self._get_connection()
        try:
            p_norm = balances_path.replace("\\", "/")
            return con.execute(f"SELECT * FROM read_parquet('{p_norm}') ORDER BY ABS(net_inventory) DESC LIMIT ?", [limit]).df().to_dict(orient="records")
        finally:
            con.close()

    def list_transactions(self, officer: Optional[str] = None, commodity: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns extracted transactions filtered by officer or commodity."""
        tx_path = os.path.join(self.processed_dir, "transactions.parquet")
        if not os.path.exists(tx_path):
            return []

        con = self._get_connection()
        try:
            p_norm = tx_path.replace("\\", "/")
            clauses = []
            params = []
            if officer:
                clauses.append("(source_official ILIKE ? OR recipient_official ILIKE ?)")
                off_pat = f"%{officer}%"
                params.extend([off_pat, off_pat])
            if commodity:
                clauses.append("commodity ILIKE ?")
                params.append(f"%{commodity}%")
            where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            query = f"SELECT * FROM read_parquet('{p_norm}') {where} LIMIT ?"
            params.append(limit)
            return con.execute(query, params).df().to_dict(orient="records")
        finally:
            con.close()
