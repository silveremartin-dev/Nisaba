"""
Sumerian Metrology and Metric Unit Conversion Engine.
Parses capacity (Gur, Barig, Ban2, Sila3), weight (Gu2, Ma-na, Gin2, Sze),
and sexagesimal discrete counts, providing verified modern metric conversions.
"""

import re
from typing import Any, Dict, List, Optional


class MetrologyEngine:
    """Parses formulaic Sumerian metrological expressions and converts to metric equivalents."""

    # Capacity ratios based on canonical Ur III imperial standard:
    # 1 gur = 300 sila3 (~300 liters)
    # 1 barig = 60 sila3 (~60 liters)
    # 1 ban2 = 10 sila3 (~10 liters)
    # 1 sila3 = 1 liter
    CAPACITY_BARLEY_KG_PER_LITER = 0.62  # Average ancient barley density ~0.62 kg/L

    # Weight ratios based on canonical Ur III mina standard:
    # 1 gu2 (talent) = 60 ma-na (~30,000 g / 30 kg)
    # 1 ma-na (mina) = 60 gin2 (~500 g)
    # 1 gin2 (shekel) = 180 sze (~8.333 g)
    # 1 sze (grain) = ~0.046 g

    RE_CAPACITY = re.compile(
        r"(\d+)?(?:\((?:asz|disz)\))?\s*(\d+)?(?:\(barig\))?\s*(\d+)?(?:\(ban2\))?\s*(\d+)?(?:\(sila3\))?\s+(sze|zi3|kasz|munu4|i3|dida)",
        re.IGNORECASE
    )

    RE_WEIGHT = re.compile(
        r"(\d+(?:/\d+)?)\((?:disz|u|asz)\)\s+(gu2|ma-na|gin2)\s+(ku3-babbar|ku3-sig17|siki|uruda|zabar)",
        re.IGNORECASE
    )

    RE_DISCRETE = re.compile(
        r"(\d+(?:/\d+)?)\((?:disz|u|gesz2|gesz\'u)\)\s+([a-z0-9_\-\{\}]+)",
        re.IGNORECASE
    )

    def parse_tablet_metrology(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extracts and converts all metrological statements across tablet lines."""
        results = []

        for l in lines:
            raw = l.get("raw_text") or l.get("normalized_text") or ""
            line_no = l.get("line_number", "")

            # 1. Capacity matches (Cereal / Liquids)
            for m in self.RE_CAPACITY.finditer(raw):
                gur = float(m.group(1)) if m.group(1) else 0.0
                barig = float(m.group(2)) if m.group(2) else 0.0
                ban2 = float(m.group(3)) if m.group(3) else 0.0
                sila = float(m.group(4)) if m.group(4) else 0.0
                commodity = m.group(5).lower()

                total_sila = (gur * 300.0) + (barig * 60.0) + (ban2 * 10.0) + sila
                if total_sila > 0:
                    liters = total_sila
                    kg_approx = round(liters * self.CAPACITY_BARLEY_KG_PER_LITER, 1) if commodity in ("sze", "zi3") else None
                    results.append({
                        "line": line_no,
                        "type": "Capacity (Volume)",
                        "ancient_expression": m.group(0).strip(),
                        "commodity": commodity,
                        "ancient_units": f"{total_sila:.0f} sila3 ({total_sila / 300.0:.2f} gur)",
                        "metric_equivalent": f"~{liters:,.0f} Liters" + (f" (~{kg_approx:,.0f} kg)" if kg_approx else ""),
                    })

            # 2. Weight matches (Precious metals, wool, bronze)
            for m in self.RE_WEIGHT.finditer(raw):
                val_tok = m.group(1)
                unit = m.group(2).lower()
                commodity = m.group(3).lower()

                qty = float(val_tok.split("/")[0]) / float(val_tok.split("/")[1]) if "/" in val_tok else float(val_tok)

                grams = 0.0
                if unit == "gu2":
                    grams = qty * 30000.0
                elif unit == "ma-na":
                    grams = qty * 500.0
                elif unit == "gin2":
                    grams = qty * 8.333

                results.append({
                    "line": line_no,
                    "type": "Weight (Mass)",
                    "ancient_expression": m.group(0).strip(),
                    "commodity": commodity,
                    "ancient_units": f"{qty} {unit}",
                    "metric_equivalent": f"~{grams:,.1f} g" if grams < 1000 else f"~{grams / 1000.0:,.2f} kg",
                })

            # 3. Discrete count matches (Livestock, personnel, objects)
            for m in self.RE_DISCRETE.finditer(raw):
                tok_qty = m.group(1)
                comm = m.group(2).lower()
                if comm in ("udu", "masz2", "gu4", "sila4", "ab2", "eme6", "gurusz", "geme2", "sa"):
                    qty = float(tok_qty.split("/")[0]) / float(tok_qty.split("/")[1]) if "/" in tok_qty else float(tok_qty)
                    results.append({
                        "line": line_no,
                        "type": "Discrete Count",
                        "ancient_expression": m.group(0).strip(),
                        "commodity": comm,
                        "ancient_units": f"{qty:g} units",
                        "metric_equivalent": f"{int(qty)} head / units",
                    })

        return results[:8]  # Top representative measures
