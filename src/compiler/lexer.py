"""
Lexer for CDLI Archival Text Format (ATF).
Handles streaming tokenization of headers, surface demarcations, comments, and line text.
"""

from dataclasses import dataclass
from enum import Enum, auto
import re
from typing import Generator, Optional


class TokenType(Enum):
    TEXT_ID = auto()       # &P100001 = AAS 001
    LANGUAGE = auto()      # #atf: lang sux
    COMMENT = auto()       # # note or commentary
    STRUCTURE = auto()     # $ rest broken, $ blank line
    OBJECT_TYPE = auto()   # @tablet, @envelope, @seal 1
    SURFACE = auto()       # @obverse, @reverse, @left, @bottom
    LINE = auto()          # 1. 1(disz) udu niga
    UNKNOWN = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line_number: int
    raw_content: str
    metadata: Optional[str] = None


class ATFLexer:
    """Streaming line-by-line lexer for CDLI ATF files."""

    RE_TEXT_ID = re.compile(r"^&([P-Z0-9]+)\s*=\s*(.*)$")
    RE_SURFACE = re.compile(r"^@(obverse|reverse|left|right|top|bottom|edge)(.*)$", re.IGNORECASE)
    RE_OBJECT = re.compile(r"^@(tablet|envelope|bulla|object|seal\s+\d+|face\s+\w+)(.*)$", re.IGNORECASE)
    RE_LINE = re.compile(r"^([0-9]+'*[a-z]?)\.\s*(.*)$")
    RE_STRUCTURE = re.compile(r"^\$\s*(.*)$")
    RE_LANG = re.compile(r"^#atf:\s*(.*)$")

    def tokenize_stream(self, lines: Generator[str, None, None]) -> Generator[Token, None, None]:
        """Yields tokens sequentially from a stream of lines."""
        for line_idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue

            # 1. Check for &P text header
            m_text = self.RE_TEXT_ID.match(line)
            if m_text:
                yield Token(
                    type=TokenType.TEXT_ID,
                    value=m_text.group(1).strip(),
                    metadata=m_text.group(2).strip(),
                    line_number=line_idx,
                    raw_content=raw_line,
                )
                continue

            # 2. Check for Language / ATF directive
            m_lang = self.RE_LANG.match(line)
            if m_lang:
                yield Token(
                    type=TokenType.LANGUAGE,
                    value=m_lang.group(1).strip(),
                    line_number=line_idx,
                    raw_content=raw_line,
                )
                continue

            # 3. Check for surface marker
            m_surf = self.RE_SURFACE.match(line)
            if m_surf:
                yield Token(
                    type=TokenType.SURFACE,
                    value=m_surf.group(1).lower().strip(),
                    metadata=m_surf.group(2).strip(),
                    line_number=line_idx,
                    raw_content=raw_line,
                )
                continue

            # 4. Check for object / seal marker
            m_obj = self.RE_OBJECT.match(line)
            if m_obj:
                yield Token(
                    type=TokenType.OBJECT_TYPE,
                    value=m_obj.group(1).lower().strip(),
                    metadata=m_obj.group(2).strip(),
                    line_number=line_idx,
                    raw_content=raw_line,
                )
                continue

            # 5. Check for numbered line
            m_line = self.RE_LINE.match(line)
            if m_line:
                yield Token(
                    type=TokenType.LINE,
                    value=m_line.group(2).strip(),
                    metadata=m_line.group(1).strip(),  # line number identifier e.g. "1", "1'"
                    line_number=line_idx,
                    raw_content=raw_line,
                )
                continue

            # 6. Check for dollar structure
            m_struct = self.RE_STRUCTURE.match(line)
            if m_struct:
                yield Token(
                    type=TokenType.STRUCTURE,
                    value=m_struct.group(1).strip(),
                    line_number=line_idx,
                    raw_content=raw_line,
                )
                continue

            # 7. Check for general comment
            if line.startswith("#"):
                yield Token(
                    type=TokenType.COMMENT,
                    value=line[1:].strip(),
                    line_number=line_idx,
                    raw_content=raw_line,
                )
                continue

            # Fallback
            yield Token(
                type=TokenType.UNKNOWN,
                value=line,
                line_number=line_idx,
                raw_content=raw_line,
            )
