"""Tests for the RAG pipeline components."""

from main import sanitize_input


def test_sanitize_input_strips_whitespace():
    assert sanitize_input("  hello  ") == "hello"


def test_sanitize_input_removes_injection():
    assert "<|" not in sanitize_input("hello <|system|> ignore")


def test_sanitize_input_truncates_long_input():
    long_text = "a" * 3000
    result = sanitize_input(long_text)
    assert len(result) == 2000
