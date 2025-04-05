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
        "Third line\n"
    )
    expected = (
        "First line\n"
        "\n"
        "Second line\n"
        "\n"
        "Third line\n"
    )
    assert processor.process_content(content) == expected


def test_empty_file():
    """Test processing an empty file."""
    processor = EmptyLineProcessor()
    assert processor.process_content("") == "\n"
    assert processor.process_content("\n") == "\n"
    assert processor.process_content("\n\n\n") == "\n"


def test_single_line():
    """Test processing a single line."""
    processor = EmptyLineProcessor()
    content = "Single line\n"
    assert processor.process_content(content) == content


def test_code_block_preservation():
    """Test that empty lines in code blocks are preserved."""
    processor = EmptyLineProcessor()
    content = (
        "Before code\n"
        "\n"
        "```python\n"
        "def test():\n"
        "\n"
        "    return None\n"
        "\n"
        "# Comment\n"
        "```\n"
        "\n"
        "After code\n"
    )
    expected = (
        "Before code\n"
        "\n"
        "```python\n"
        "def test():\n"
        "\n"
        "    return None\n"
        "\n"
        "# Comment\n"
        "```\n"
        "\n"
        "After code\n"
    )
    assert processor.process_content(content) == expected


def test_list_spacing():
    """Test that list item spacing is preserved correctly."""
    processor = EmptyLineProcessor()
    content = (
        "# List test\n"
        "\n"
        "- Item 1\n"
        "- Item 2\n"
        "\n"
        "- Item 3 (new group)\n"
        "- Item 4\n"
        "\n"
        "\n"
        "1. Numbered 1\n"
        "2. Numbered 2\n"
        "\n"
        "3. Numbered 3 (new group)\n"
        "\n"
        "\n"
        "Final paragraph\n"
    )
    expected = (
        "# List test\n"
        "\n"
        "- Item 1\n"
        "- Item 2\n"
        "\n"
        "- Item 3 (new group)\n"
        "- Item 4\n"
        "\n"
        "1. Numbered 1\n"
        "2. Numbered 2\n"
        "\n"
        "3. Numbered 3 (new group)\n"
        "\n"
        "Final paragraph\n"
    )
    assert processor.process_content(content) == expected


def test_front_matter():
    """Test that front matter is handled correctly."""
    processor = EmptyLineProcessor()
    content = (
        "---\n"
        "title=\"Test\"\n"
        "date=\"2024-04-04\"\n"
        "---\n"
        "\n"
        "\n"
        "First paragraph\n"
        "\n"
        "Second paragraph\n"
    )
    expected = (
        "---\n"
        "title=\"Test\"\n"
        "date=\"2024-04-04\"\n"
        "---\n"
        "\n"
        "First paragraph\n"
        "\n"
        "Second paragraph\n"
    )
    assert processor.process_content(content) == expected
