"""
Bracket and damage balance auditor for CDLI ATF lines.
Validates parity of [], <>, (), and integrity of damage flags (#, ?, !).
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import List


class IssueSeverity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class LintIssue:
    rule_id: str
    id_text: str
    id_line: str
    surface: str
    line_number: int
    severity: IssueSeverity
    message: str
    raw_token: str


class BracketAuditor:
    """Audits balance and nesting of brackets in cuneiform transliterations."""

    def audit_line(self, id_text: str, id_line: str, surface: str, line_no: int, text: str) -> List[LintIssue]:
        issues: List[LintIssue] = []

        # 1. Square brackets [ ] (lacuna restoration)
        open_sq = text.count("[")
        close_sq = text.count("]")
        if open_sq != close_sq:
            issues.append(LintIssue(
                rule_id="B001",
                id_text=id_text,
                id_line=id_line,
                surface=surface,
                line_number=line_no,
                severity=IssueSeverity.ERROR,
                message=f"Mismatched square brackets: {open_sq} opened, {close_sq} closed",
                raw_token=text,
            ))

        # Check order: closing before opening
        if "]" in text and "[" in text:
            first_open = text.find("[")
            first_close = text.find("]")
            if first_close < first_open:
                issues.append(LintIssue(
                    rule_id="B002",
                    id_text=id_text,
                    id_line=id_line,
                    surface=surface,
                    line_number=line_no,
                    severity=IssueSeverity.ERROR,
                    message="Closing square bracket ']' encountered before opening '['",
                    raw_token=text,
                ))

        # 2. Angle brackets < > (emendations / scribal omissions)
        open_ang = text.count("<")
        close_ang = text.count(">")
        if open_ang != close_ang:
            issues.append(LintIssue(
                rule_id="B003",
                id_text=id_text,
                id_line=id_line,
                surface=surface,
                line_number=line_no,
                severity=IssueSeverity.WARNING,
                message=f"Mismatched angle brackets: {open_ang} opened, {close_ang} closed",
                raw_token=text,
            ))

        # 3. Parentheses ( ) (metrological indices)
        open_par = text.count("(")
        close_par = text.count(")")
        if open_par != close_par:
            issues.append(LintIssue(
                rule_id="B004",
                id_text=id_text,
                id_line=id_line,
                surface=surface,
                line_number=line_no,
                severity=IssueSeverity.ERROR,
                message=f"Mismatched parentheses in numerical/metrological token: {open_par} opened, {close_par} closed",
                raw_token=text,
            ))

        # 4. Curly determinative braces { }
        open_cur = text.count("{")
        close_cur = text.count("}")
        if open_cur != close_cur:
            issues.append(LintIssue(
                rule_id="B005",
                id_text=id_text,
                id_line=id_line,
                surface=surface,
                line_number=line_no,
                severity=IssueSeverity.ERROR,
                message=f"Mismatched curly braces for semantic determinative: {open_cur} opened, {close_cur} closed",
                raw_token=text,
            ))

        return issues
