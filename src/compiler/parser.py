"""
AST Parser for CDLI ATF files.
Constructs structured Tablet, Line, and Sign dataclasses with preservation metrics.
"""

from dataclasses import dataclass, field
import re
from typing import Dict, Generator, List, Optional
from src.compiler.lexer import ATFLexer, Token, TokenType


@dataclass
class SignRecord:
    id_sign: str
    id_line: str
    sign_index: int
    token: str
    clean_value: str
    sign_type: str  # NUMERIC, LOGOGRAM, SYLLABLE, DETERMINATIVE, UNKNOWN
    damage_flag: Optional[str] = None  # #, ?, !
    is_broken: bool = False  # True if inside [...]


@dataclass
class LineRecord:
    id_line: str
    id_text: str
    surface: str
    line_number: int
    line_label: str  # e.g. "1", "1'", "2a"
    raw_text: str
    normalized_text: str
    is_damaged: bool
    signs: List[SignRecord] = field(default_factory=list)


@dataclass
class TabletRecord:
    id_text: str
    designation: str
    language: str = "sux"
    period: str = "Ur III (ca. 2100-2000 BC)"
    provenance: str = "Unassigned"
    lines: List[LineRecord] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    has_date: bool = False


class ATFParser:
    """Parses token streams into fully structured Tablet, Line, and Sign AST models."""

    RE_NUMERIC = re.compile(r"^\d+\([a-z0-9\']+\)$", re.IGNORECASE)
    RE_LOGOGRAM = re.compile(r"^[A-Z0-9_\-\.\/]+$")
    RE_DETERMINATIVE = re.compile(r"^\{([a-z0-9_\-]+)\}$")

    @staticmethod
    def _clean_token(raw_token: str) -> str:
        """Removes brackets and damage flags from token, preserving metrological parentheses."""
        cleaned = re.sub(r"[\[\]\<\>#\?!]", "", raw_token)
        return cleaned.strip()

    def _classify_sign(self, token: str, clean_val: str) -> str:
        """Classifies a sign into standard linguistic categories."""
        if re.match(r"^\d+(\([a-z0-9\']+\))?$", clean_val, re.IGNORECASE):
            return "NUMERIC"
        if self.RE_DETERMINATIVE.match(token) or (clean_val.startswith("{") and clean_val.endswith("}")):
            return "DETERMINATIVE"
        if self.RE_LOGOGRAM.match(clean_val):
            return "LOGOGRAM"
        if any(c.islower() for c in clean_val):
            return "SYLLABLE"
        return "UNKNOWN"

    def _parse_signs(self, id_line: str, line_text: str) -> List[SignRecord]:
        """Tokenizes line text into individual SignRecords with damage tagging."""
        tokens = line_text.split()
        signs: List[SignRecord] = []
        is_inside_bracket = False

        for idx, tok in enumerate(tokens):
            if "[" in tok:
                is_inside_bracket = True

            clean_val = self._clean_token(tok)
            if not clean_val or clean_val in ("...", "x", "X"):
                damage = "#" if "#" in tok else None
                sign = SignRecord(
                    id_sign=f"{id_line}_{idx}",
                    id_line=id_line,
                    sign_index=idx,
                    token=tok,
                    clean_value=clean_val or "x",
                    sign_type="LACUNA" if clean_val in ("...", "x", "X") else "UNKNOWN",
                    damage_flag=damage,
                    is_broken=True if (is_inside_bracket or "[" in tok) else False,
                )
            else:
                damage = None
                if "#" in tok:
                    damage = "#"
                elif "?" in tok:
                    damage = "?"
                elif "!" in tok:
                    damage = "!"

                sign_type = self._classify_sign(tok, clean_val)
                sign = SignRecord(
                    id_sign=f"{id_line}_{idx}",
                    id_line=id_line,
                    sign_index=idx,
                    token=tok,
                    clean_value=clean_val,
                    sign_type=sign_type,
                    damage_flag=damage,
                    is_broken=is_inside_bracket,
                )

            signs.append(sign)

            if "]" in tok:
                is_inside_bracket = False

        return signs

    def parse_stream(self, token_stream: Generator[Token, None, None]) -> Generator[TabletRecord, None, None]:
        """Consumes a Token stream and yields parsed TabletRecord objects."""
        current_tablet: Optional[TabletRecord] = None
        current_surface: str = "obverse"
        line_counter: int = 0

        for tok in token_stream:
            if tok.type == TokenType.TEXT_ID:
                if current_tablet:
                    yield current_tablet
                current_tablet = TabletRecord(
                    id_text=tok.value,
                    designation=tok.metadata or tok.value,
                )
                current_surface = "obverse"
                line_counter = 0

            elif tok.type == TokenType.LANGUAGE and current_tablet:
                current_tablet.language = tok.value

            elif tok.type == TokenType.SURFACE:
                current_surface = tok.value

            elif tok.type == TokenType.OBJECT_TYPE:
                if "seal" in tok.value:
                    current_surface = tok.value

            elif tok.type == TokenType.LINE and current_tablet:
                line_counter += 1
                raw_text = tok.value
                line_label = tok.metadata or str(line_counter)
                id_line = f"{current_tablet.id_text}_{current_surface}_{line_counter}"

                clean_text = self._clean_token(raw_text)
                is_damaged = any(c in raw_text for c in ("[", "]", "#", "?", "x", "..."))

                signs = self._parse_signs(id_line, raw_text)

                # Check if this line is an explicit date formula
                if raw_text.startswith("mu ") or " mu-hul" in raw_text or " ba-hun" in raw_text or " ba-du3" in raw_text:
                    if "[" not in raw_text or "]" in raw_text:
                        current_tablet.has_date = True

                line_rec = LineRecord(
                    id_line=id_line,
                    id_text=current_tablet.id_text,
                    surface=current_surface,
                    line_number=line_counter,
                    line_label=line_label,
                    raw_text=raw_text,
                    normalized_text=clean_text,
                    is_damaged=is_damaged,
                    signs=signs,
                )
                current_tablet.lines.append(line_rec)

        if current_tablet:
            yield current_tablet

    def parse_file(self, filepath: str) -> List[TabletRecord]:
        """Convenience method to parse an entire ATF file from disk."""
        lexer = ATFLexer()
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            tokens = lexer.tokenize_stream((line for line in f))
            return list(self.parse_stream(tokens))
