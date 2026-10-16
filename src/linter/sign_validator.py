"""
Cuneiform sign and orthographic validator.
Validates sign tokens against CDLI Canonical ATF rules, compound signs (|A.EDIN|), and number formats.
"""

import re
from typing import List
from src.linter.bracket_auditor import IssueSeverity, LintIssue


class SignValidator:
    """Validates individual sign tokens against Assyriological transliteration rules."""

    RE_VALID_NUMBER = re.compile(r"^\d+(\([a-z0-9\']+\))(\-kam)?$", re.IGNORECASE)
    RE_BAD_SUBSCRIPT = re.compile(r"[a-z]+_[0-9]+", re.IGNORECASE)
    RE_COMPOUND = re.compile(r"^\|.*\|$")

    def audit_tokens(self, id_text: str, id_line: str, surface: str, line_no: int, text: str) -> List[LintIssue]:
        issues: List[LintIssue] = []
        tokens = text.split()

        for tok in tokens:
            # Check for bad subscript syntax like gu_4 instead of gu4
            if self.RE_BAD_SUBSCRIPT.search(tok):
                issues.append(LintIssue(
                    rule_id="S001",
                    id_text=id_text,
                    id_line=id_line,
                    surface=surface,
                    line_number=line_no,
                    severity=IssueSeverity.WARNING,
                    message=f"Illegal subscript underscore notation in token '{tok}' (use standard ASCII index e.g. 'gu4')",
                    raw_token=tok,
                ))

            # Check compound sign delimiters |SIGN.SIGN|
            if ("|" in tok) and not (tok.startswith("|") and tok.endswith("|")):
                issues.append(LintIssue(
                    rule_id="S002",
                    id_text=id_text,
                    id_line=id_line,
                    surface=surface,
                    line_number=line_no,
                    severity=IssueSeverity.ERROR,
                    message=f"Malformed compound sign delimiter '|' in '{tok}' (compound signs must be enclosed |...|)",
                    raw_token=tok,
                ))

            # Check unformatted number token like 1disz instead of 1(disz)
            clean_tok = re.sub(r"[\[\]#\?!]", "", tok)
            if re.match(r"^\d+[a-zA-Z]+$", clean_tok) and not re.match(r"^\d+(disz|u|gesz2|sila3|ban2|barig|gur)$", clean_tok):
                # Potential unparenthesized number e.g. 5udu
                if re.match(r"^\d+(udu|masz2|sila4|gu4|ab2|sze)$", clean_tok):
                    issues.append(LintIssue(
                        rule_id="S003",
                        id_text=id_text,
                        id_line=id_line,
                        surface=surface,
                        line_number=line_no,
                        severity=IssueSeverity.ERROR,
                        message=f"Missing space/parenthesis between numeral and commodity in '{tok}' (e.g. use '1(disz) {clean_tok[1:]}')",
                        raw_token=tok,
                    ))

        return issues
