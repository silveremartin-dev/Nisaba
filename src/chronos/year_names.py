"""
Year formula catalog and normalizer for the Ur III period (ca. 2112–2004 BC).
Normalizes verbose and abbreviated royal year names into canonical King and Regnal Year codes.
"""

from dataclasses import dataclass
import re
from typing import Dict, List, Optional


@dataclass
class YearFormula:
    king: str          # UN (Ur-Nammu), SH (Shulgi), AS (Amar-Suen), SS (Shu-Suen), IS (Ibbi-Suen)
    regnal_year: int   # 1 to 48
    code: str          # e.g. "AS02", "SS03"
    canonical_name: str
    patterns: List[str]


# Core Ur III Year Formula Catalog (Key attested administrative years)
YEAR_CATALOG: List[YearFormula] = [
    # Shulgi
    YearFormula("SH", 44, "SH44", "mu si-mu-ru-um{ki} lu-lu-bu{ki} a-ra2 1(u) la2 1(disz)-kam-asz ba-hul", ["si-mu-ru-um", "lu-lu-bu"]),
    YearFormula("SH", 45, "SH45", "mu ur-bi2-lum{ki} ba-hul", ["ur-bi2-lum{ki} ba-hul"]),
    YearFormula("SH", 46, "SH46", "mu ki-masz{ki} ba-hul", ["ki-masz{ki} ba-hul"]),
    YearFormula("SH", 47, "SH47", "mu us2-sa ki-masz{ki} ba-hul", ["us2-sa ki-masz"]),
    YearFormula("SH", 48, "SH48", "mu ha-ar-szi{ki} hu-ur5-ti{ki} ba-hul", ["ha-ar-szi", "hu-ur5-ti"]),
    # Amar-Suen
    YearFormula("AS", 1, "AS01", "mu {d}amar-{d}suen lugal", ["{d}amar-{d}suen lugal$"]),
    YearFormula("AS", 2, "AS02", "mu {d}amar-{d}suen lugal-e ur-bi2-lum{ki} mu-hul", ["ur-bi2-lum{ki} mu-hul"]),
    YearFormula("AS", 3, "AS03", "mu {d}amar-{d}suen lugal-e {gesz}gu-za {d}en-lil2-la2 in-dim2", ["{gesz}gu-za {d}en-lil2"]),
    YearFormula("AS", 4, "AS04", "mu en-mah-gal-an-na en {d}nanna ba-hun", ["en-mah-gal-an-na"]),
    YearFormula("AS", 5, "AS05", "mu en-unu6-gal {d}inanna ba-hun", ["en-unu6-gal", "en-unu6"]),
    YearFormula("AS", 6, "AS06", "mu sza-asz-ru{ki} ba-hul", ["sza-asz-ru"]),
    YearFormula("AS", 7, "AS07", "mu hu-uh2-nu-ri{ki} ba-hul", ["hu-uh2-nu-ri"]),
    YearFormula("AS", 8, "AS08", "mu en {d}nanna kar-zi-da ba-hun", ["kar-zi-da ba-hun", "kar-zi-da"]),
    YearFormula("AS", 9, "AS09", "mu en {d}inanna ba-hun", ["en {d}inanna ba-hun$"]),
    # Shu-Suen
    YearFormula("SS", 1, "SS01", "mu {d}szu-{d}suen lugal", ["{d}szu-{d}suen lugal$"]),
    YearFormula("SS", 2, "SS02", "mu {d}szu-{d}suen lugal-e ma2-dara3-abzu ba-ab-du8", ["ma2-dara3-abzu"]),
    YearFormula("SS", 3, "SS03", "mu {d}szu-{d}suen lugal uri5{ki}-ma-ke4 si-ma-num2{ki} mu-hul", ["si-ma-num2"]),
    YearFormula("SS", 4, "SS04", "mu {d}szu-{d}suen lugal-e bad3 mar-tu mu-ri-iq-ti-id-ni-im mu-du3", ["bad3 mar-tu"]),
    YearFormula("SS", 5, "SS05", "mu {d}szu-{d}suen lugal-e us2-sa bad3 mar-tu mu-du3", ["us2-sa bad3 mar-tu"]),
    YearFormula("SS", 6, "SS06", "mu {d}szu-{d}suen lugal-e na-ru2-a-mah {d}en-lil2 {d}nin-lil2-ra mu-ne-du3", ["na-ru2-a-mah"]),
    YearFormula("SS", 7, "SS07", "mu {d}szu-{d}suen lugal-e ma-da za-ab-sza-li{ki} mu-hul", ["za-ab-sza-li"]),
    YearFormula("SS", 8, "SS08", "mu {d}szu-{d}suen lugal uri5{ki}-ma-ke4 ma2-gur8-mah {d}en-lil2 {d}nin-lil2-ra mu-ne-dim2", ["ma2-gur8-mah"]),
    YearFormula("SS", 9, "SS09", "mu {d}szu-{d}suen lugal-e e2 {d}szara2 umma{ki}-ka mu-du3", ["e2 {d}szara2"]),
    # Ibbi-Suen
    YearFormula("IS", 1, "IS01", "mu {d}i-bi2-{d}suen lugal", ["{d}i-bi2-{d}suen lugal$"]),
    YearFormula("IS", 2, "IS02", "mu {d}i-bi2-{d}suen lugal-e en {d}inanna unu{ki}-ga masz2-e in-pa3", ["en {d}inanna unu{ki}"]),
    YearFormula("IS", 3, "IS03", "mu {d}i-bi2-{d}suen lugal-e simurrum{ki} mu-hul", ["simurrum{ki} mu-hul"]),
]


class YearNormalizer:
    """Matches raw ATF date lines against canonical Ur III formulas."""

    def __init__(self, catalog: Optional[List[YearFormula]] = None):
        self.catalog = catalog or YEAR_CATALOG

    def normalize(self, line_text: str) -> Optional[YearFormula]:
        """Returns the canonical YearFormula matching the text line, if identified."""
        clean = re.sub(r"[\[\]\(\)#\?!]", "", line_text).strip()
        if not (clean.startswith("mu ") or clean.startswith("mu-")):
            return None

        # Ignore damaged formulas that have no content
        content = clean[3:].strip()
        if not content or content in ("...", "x", "X"):
            return None

        for yf in self.catalog:
            for pat in yf.patterns:
                if re.search(pat, clean, re.IGNORECASE):
                    return yf

        return None
