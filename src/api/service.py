"""
Data access and business logic service layer for Nisaba REST API.
Executes high-speed queries on DuckDB and cached Parquet tables.
"""

import os
from typing import Any, Dict, List, Optional
import duckdb
import pandas as pd


from src.ledger.metrology import MetrologyEngine


class NisabaDataService:
    """Provides querying capabilities over Nisaba DuckDB tables and analytical Parquet outputs."""

    def __init__(self, db_path: str = "data/processed/nisaba.duckdb", processed_dir: str = "data/processed"):
        self.db_path = db_path
        self.processed_dir = processed_dir
        self.metrology = MetrologyEngine()

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
        category: Optional[str] = None,
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
                clean_search = search.strip()
                if clean_search.upper().startswith("P") and any(c.isdigit() for c in clean_search):
                    where_clauses.append("id_text ILIKE ?")
                    params.append(f"{clean_search}%")
                else:
                    # Check if exact match exists in transactions or author attributions
                    c_low = clean_search.lower()
                    exact_matches = con.execute("""
                        SELECT DISTINCT id_text FROM transactions 
                        WHERE source_party = ? OR receiving_party = ? OR commodity = ?
                        UNION
                        SELECT DISTINCT id_text FROM author_attributions 
                        WHERE identified_scribe = ?
                        LIMIT 3000
                    """, [c_low, c_low, c_low, clean_search]).fetchall()

                    if exact_matches:
                        matched_ids = [r[0] for r in exact_matches]
                        id_list_str = ", ".join([repr(x) for x in matched_ids])
                        where_clauses.append(f"(id_text IN ({id_list_str}) OR designation ILIKE ?)")
                        params.append(f"%{clean_search}%")
                    else:
                        where_clauses.append("(id_text ILIKE ? OR designation ILIKE ?)")
                        search_pattern = f"%{clean_search}%"
                        params.extend([search_pattern, search_pattern])

            if category == "showcase":
                showcase_ids = [
                    'P100001', 'P100002', 'P100003', 'P100004', 'P100005',
                    'P100006', 'P100007', 'P100008', 'P100009', 'P100010',
                    'P100012', 'P100014', 'P100015', 'P100089', 'P106055',
                    'P131610', 'P134231', 'P142749', 'P285811'
                ]
                where_clauses.append(f"id_text IN ({', '.join([repr(x) for x in showcase_ids])})")
            elif category == "scribes":
                where_clauses.append("id_text IN (SELECT id_text FROM author_attributions WHERE identified_scribe != 'Unknown')")
            elif category == "dates":
                where_clauses.append("id_text IN (SELECT id_text FROM chronos_estimates WHERE status IN ('CERTIFIED_DATED', 'ESTIMATED'))")
            elif category == "joins":
                where_clauses.append("id_text IN (SELECT id_text_a FROM virtual_joins UNION SELECT id_text_b FROM virtual_joins)")
            elif category == "transactions":
                where_clauses.append("id_text IN (SELECT DISTINCT id_text FROM transactions)")

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            total = con.execute(f"SELECT COUNT(*) FROM tablets {where_str}", params).fetchone()[0]
            # Prioritize Ur III chancery texts (P100000+) by default over archaic Uruk pictographs
            query = f"""
                SELECT * FROM tablets 
                {where_str} 
                ORDER BY CASE WHEN id_text LIKE 'P1%' THEN 0 ELSE 1 END, id_text 
                LIMIT ? OFFSET ?
            """
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

            # Infer Period & Provenance if unassigned
            raw_all_lines = " ".join([str(l.get("raw_text", "")) for l in tablet["lines"]]).lower()
            p_num = id_text.replace("P", "")
            if not tablet.get("period") or tablet.get("period") in ("Unassigned", "None", ""):
                if p_num.isdigit() and int(p_num) >= 100000:
                    tablet["period"] = "Ur III (ca. 2112–2004 BC)"
                elif p_num.isdigit() and int(p_num) < 6000:
                    tablet["period"] = "Uruk IV–III / Proto-Cuneiform (ca. 3200–3000 BC)"
                else:
                    tablet["period"] = "Ur III (ca. 2112–2004 BC)"

            if not tablet.get("provenance") or tablet.get("provenance") in ("Unassigned", "None", ""):
                if any(k in raw_all_lines for k in ["ab-ba-sa6-ga", "na-lu5", "in-ta-e3-a", "du11-ga", "ur-szu-ga-lam-ma", "masz-da3", "szu-esz5", "ezem-mah"]):
                    tablet["provenance"] = "Puzrish-Dagan (Drehem) — Royal Livestock Bureau"
                elif any(k in raw_all_lines for k in ["lu2-kal-la", "ur-{d}szara2", "da-da-ga", "ensi2-ka", "sze-kar", "min-esz3", "umma"]):
                    tablet["provenance"] = "Umma — Chancery & Agricultural Depot"
                elif any(k in raw_all_lines for k in ["lagasz", "girsu", "ba-zi", "ur-{d}lamma"]):
                    tablet["provenance"] = "Girsu (Lagash) — State Granary & Textiles"
                elif any(k in raw_all_lines for k in ["nibru", "gu4-si-su", "inanna"]):
                    tablet["provenance"] = "Nippur — Sacred City of Enlil"
                elif any(k in raw_all_lines for k in ["uri5", "nanna"]):
                    tablet["provenance"] = "Ur — Imperial Capital"
                else:
                    tablet["provenance"] = "Southern Mesopotamia (Sumer)"

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

            # Transactions
            tx_path = os.path.join(self.processed_dir, "transactions.parquet")
            tablet["transactions"] = []
            if os.path.exists(tx_path):
                p_norm = tx_path.replace("\\", "/")
                df_tx = con.execute(
                    f"SELECT quantity, commodity, source_party, receiving_party, action_type, month, year FROM read_parquet('{p_norm}') WHERE id_text = ?",
                    [id_text]
                ).df()
                tablet["transactions"] = df_tx.to_dict(orient="records")

            # Metrology / Measures conversion
            tablet["metrology"] = self.metrology.parse_tablet_metrology(tablet["lines"])

            # Photos & Official Source Reference
            p_clean = id_text.strip().upper()
            numeric_id = p_clean[1:] if p_clean.startswith("P") else p_clean
            local_img_path = os.path.join("assets", "real_tablets", f"{p_clean}.jpg")
            has_local = os.path.exists(local_img_path)
            tablet["photos"] = {
                "has_local_image": has_local,
                "local_image_url": f"/assets/real_tablets/{p_clean}.jpg" if has_local else None,
                "cdli_image_url": f"https://cdli.mpiwg-berlin.mpg.de/dl/photo/{p_clean}.jpg",
                "source_url": f"https://cdli.mpiwg-berlin.mpg.de/artifacts/{numeric_id}",
                "source_label": f"CDLI ({p_clean})",
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
                clauses.append("(source_party ILIKE ? OR receiving_party ILIKE ?)")
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
