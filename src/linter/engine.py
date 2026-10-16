"""
Main Linter Engine for Nisaba.
Coordinates bracket auditing, sign validation, and anomaly reporting.
"""

from dataclasses import dataclass, field
from typing import Dict, List
import pandas as pd

from src.compiler.parser import TabletRecord
from src.linter.bracket_auditor import BracketAuditor, IssueSeverity, LintIssue
from src.linter.sign_validator import SignValidator


@dataclass
class LinterReport:
    total_tablets_audited: int
    total_lines_audited: int
    total_errors: int
    total_warnings: int
    clean_tablets_count: int
    pass_rate: float
    issues: List[LintIssue] = field(default_factory=list)

    def to_dataframe(self) -> pd.DataFrame:
        """Converts issues to a Pandas DataFrame."""
        records = [
            {
                "rule_id": iss.rule_id,
                "id_text": iss.id_text,
                "id_line": iss.id_line,
                "surface": iss.surface,
                "line_number": iss.line_number,
                "severity": iss.severity.value,
                "message": iss.message,
                "raw_token": iss.raw_token,
            }
            for iss in self.issues
        ]
        return pd.DataFrame(records)


class LinterEngine:
    """Orchestrates comprehensive linguistic and syntactic linting of Sumerian tablets."""

    def __init__(self):
        self.bracket_auditor = BracketAuditor()
        self.sign_validator = SignValidator()

    def audit_tablet(self, tablet: TabletRecord) -> List[LintIssue]:
        """Audits a single tablet, returning all discovered issues."""
        tablet_issues: List[LintIssue] = []
        for line in tablet.lines:
            b_issues = self.bracket_auditor.audit_line(
                id_text=tablet.id_text,
                id_line=line.id_line,
                surface=line.surface,
                line_no=line.line_number,
                text=line.raw_text,
            )
            s_issues = self.sign_validator.audit_tokens(
                id_text=tablet.id_text,
                id_line=line.id_line,
                surface=line.surface,
                line_no=line.line_number,
                text=line.raw_text,
            )
            tablet_issues.extend(b_issues)
            tablet_issues.extend(s_issues)
        return tablet_issues

    def audit_corpus(self, tablets: List[TabletRecord]) -> LinterReport:
        """Audits a corpus of tablets and produces a summary report."""
        all_issues: List[LintIssue] = []
        clean_tablets = 0
        total_lines = 0

        for tab in tablets:
            total_lines += len(tab.lines)
            tab_issues = self.audit_tablet(tab)
            if not tab_issues:
                clean_tablets += 1
            all_issues.extend(tab_issues)

        error_count = sum(1 for iss in all_issues if iss.severity == IssueSeverity.ERROR)
        warning_count = sum(1 for iss in all_issues if iss.severity == IssueSeverity.WARNING)

        total_tabs = len(tablets)
        pass_rate = (clean_tablets / total_tabs * 100.0) if total_tabs > 0 else 0.0

        return LinterReport(
            total_tablets_audited=total_tabs,
            total_lines_audited=total_lines,
            total_errors=error_count,
            total_warnings=warning_count,
            clean_tablets_count=clean_tablets,
            pass_rate=pass_rate,
            issues=all_issues,
        )
