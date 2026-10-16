"""Tests for LinterEngine, BracketAuditor, and SignValidator."""

import pytest
from src.compiler.parser import ATFParser
from src.linter.bracket_auditor import BracketAuditor, IssueSeverity
from src.linter.sign_validator import SignValidator
from src.linter.engine import LinterEngine


def test_bracket_auditor():
    auditor = BracketAuditor()

    # Mismatched square brackets
    iss1 = auditor.audit_line("P1", "L1", "obverse", 1, "1(disz) [udu niga")
    assert any(i.rule_id == "B001" and i.severity == IssueSeverity.ERROR for i in iss1)

    # Closing before opening
    iss2 = auditor.audit_line("P1", "L1", "obverse", 1, "1(disz) ]udu [niga")
    assert any(i.rule_id == "B002" for i in iss2)

    # Mismatched curly determinative
    iss3 = auditor.audit_line("P1", "L1", "obverse", 1, "mu {d}szu-{d}suen lugal {d")
    assert any(i.rule_id == "B005" for i in iss3)


def test_sign_validator():
    validator = SignValidator()

    # Illegal subscript
    iss1 = validator.audit_tokens("P1", "L1", "obverse", 1, "1(disz) gu_4 niga")
    assert any(i.rule_id == "S001" for i in iss1)

    # Malformed compound sign
    iss2 = validator.audit_tokens("P1", "L1", "obverse", 1, "1(disz) |A.EDIN")
    assert any(i.rule_id == "S002" for i in iss2)

    # Missing space/parenthesis
    iss3 = validator.audit_tokens("P1", "L1", "obverse", 1, "5udu niga")
    assert any(i.rule_id == "S003" for i in iss3)


def test_linter_corpus_report():
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    linter = LinterEngine()
    report = linter.audit_corpus(tablets)

    assert report.total_tablets_audited == 7
    assert report.total_lines_audited > 0
    assert isinstance(report.pass_rate, float)
