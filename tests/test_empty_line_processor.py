import pytest
from wx.empty_line_processor import EmptyLineProcessor


def test_basic_empty_line_removal():
    """Test basic empty line removal functionality."""
    processor = EmptyLineProcessor()
    content = (
        "First line\n"
        "\n"
        "\n"
        "Second line\n"
        "\n"
        "\n"
        "\n"
        "Third line"
    )
    expected = (
        "First line\n"
        "\n"
        "Second line\n"
        "\n"
        "Third line"
    )
    assert processor.process_content(content) == expected


def test_empty_file():
    """Test processing an empty file."""
    processor = EmptyLineProcessor()
    assert processor.process_content("") == ""
    assert processor.process_content("\n") == ""
    assert processor.process_content("\n\n\n") == ""


def test_single_line():
    """Test processing a single line."""
    processor = EmptyLineProcessor()
    content = "Single line\n"
    assert processor.process_content(content) == content
