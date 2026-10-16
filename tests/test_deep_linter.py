"""Deep tests for Linter edge cases, bracket nesting, and orthography."""

import pytest
from src.linter.bracket_auditor import BracketAuditor, IssueSeverity
from src.linter.sign_validator import SignValidator


def test_linter_unmatched_angle_brackets():
    auditor = BracketAuditor()
    issues = auditor.audit_line("P1", "L1", "obverse", 1, "1(disz) <udu niga")
    assert any(i.rule_id == "B003" and i.severity == IssueSeverity.WARNING for i in issues)


def test_linter_unmatched_parentheses():
    auditor = BracketAuditor()
    issues = auditor.audit_line("P1", "L1", "obverse", 1, "1(disz udu niga")
    assert any(i.rule_id == "B004" and i.severity == IssueSeverity.ERROR for i in issues)


def test_sign_validator_multiple_issues():
    validator = SignValidator()
    # Line with illegal subscript and glued number
    issues = validator.audit_tokens("P1", "L1", "obverse", 1, "5udu gu_4")
    assert len(issues) >= 2
    assert any(i.rule_id == "S001" for i in issues)
    assert any(i.rule_id == "S003" for i in issues)
