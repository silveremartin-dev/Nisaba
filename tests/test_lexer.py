"""Tests for ATFLexer streaming tokenization."""

import pytest
from src.compiler.lexer import ATFLexer, TokenType


def test_lexer_basic_tokens():
    raw_lines = [
        "&P100001 = AAS 001\n",
        "#atf: lang sux\n",
        "# this is a comment\n",
        "@tablet\n",
        "@obverse\n",
        "1. 1(disz) udu niga\n",
        "$ blank line\n",
        "@reverse\n",
        "1. ki ab-ba-sa6-ga-ta\n",
    ]
    lexer = ATFLexer()
    tokens = list(lexer.tokenize_stream((l for l in raw_lines)))

    assert len(tokens) == 9
    assert tokens[0].type == TokenType.TEXT_ID
    assert tokens[0].value == "P100001"
    assert tokens[0].metadata == "AAS 001"

    assert tokens[1].type == TokenType.LANGUAGE
    assert tokens[1].value == "lang sux"

    assert tokens[2].type == TokenType.COMMENT

    assert tokens[3].type == TokenType.OBJECT_TYPE
    assert tokens[3].value == "tablet"

    assert tokens[4].type == TokenType.SURFACE
    assert tokens[4].value == "obverse"

    assert tokens[5].type == TokenType.LINE
    assert tokens[5].metadata == "1"
    assert tokens[5].value == "1(disz) udu niga"

    assert tokens[6].type == TokenType.STRUCTURE
    assert tokens[7].type == TokenType.SURFACE
    assert tokens[7].value == "reverse"


def test_lexer_broken_numbering():
    raw_lines = [
        "1'. 2(disz) masz2\n",
        "2a. ki ur-mes-ta\n",
    ]
    lexer = ATFLexer()
    tokens = list(lexer.tokenize_stream((l for l in raw_lines)))
    assert len(tokens) == 2
    assert tokens[0].metadata == "1'"
    assert tokens[1].metadata == "2a"
