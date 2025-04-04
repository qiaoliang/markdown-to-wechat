import os
import tempfile
import pytest
from pathlib import Path
from typing import Dict, Any
from tempfile import NamedTemporaryFile

from wx.hugo_processor import HugoProcessor, FormatViolation


def test_hugo_processor_initialization_with_valid_config():
    # Arrange
    config = {
        'source_dir': '/path/to/source',
        'target_dir': '/path/to/target',
        'image_dir': '/path/to/images'
    }

    # Act
    processor = HugoProcessor(config)

    # Assert
    assert processor.config == config
    assert processor.logger is not None


def test_hugo_processor_initialization_with_missing_config():
    # Arrange
    invalid_configs = [
        {},  # Empty config
        {'source_dir': '/path/to/source'},  # Missing target_dir and image_dir
        {'source_dir': '/path/to/source',
            'target_dir': '/path/to/target'},  # Missing image_dir
        {'target_dir': '/path/to/target',
            'image_dir': '/path/to/images'},  # Missing source_dir
    ]

    # Act & Assert
    for config in invalid_configs:
        with pytest.raises(ValueError) as exc_info:
            HugoProcessor(config)
        assert "Missing required config keys" in str(exc_info.value)


def test_hugo_processor_initialization_with_invalid_paths():
    # Arrange
    config = {
        'source_dir': '',  # Empty path
        'target_dir': '/path/to/target',
        'image_dir': '/path/to/images'
    }

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        HugoProcessor(config)
    assert "Invalid path" in str(exc_info.value)


def create_temp_markdown_file(content: str) -> Path:
    """Helper function to create a temporary markdown file with given content."""
    temp_file = NamedTemporaryFile(delete=False, suffix='.md')
    temp_file.write(content.encode('utf-8'))
    temp_file.close()
    return Path(temp_file.name)


def test_check_format_with_consistent_key_value_format():
    # Arrange
    content = """---
title="Test Article"
description="A test article"
date="2024-04-04"
---
# Content here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    violations = processor.check_format(md_file)

    # Assert
    assert len(violations) == 0

    # Cleanup
    md_file.unlink()


def test_check_format_with_mixed_formats():
    # Arrange
    content = """---
title="Test Article"
description: A test article
date="2024-04-04"
---
# Content here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    violations = processor.check_format(md_file)

    # Assert
    assert len(violations) == 1
    violation = violations[0]
    assert isinstance(violation, FormatViolation)
    assert violation.line_number == 3  # The line with 'description: A test article'
    assert "Mixed format" in violation.message
    assert "description: A test article" in violation.message

    # Cleanup
    md_file.unlink()


def test_check_format_with_missing_front_matter():
    # Arrange
    content = """# Just content
No front matter here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    violations = processor.check_format(md_file)

    # Assert
    assert len(violations) == 1
    violation = violations[0]
    assert isinstance(violation, FormatViolation)
    assert violation.line_number == 1
    assert "Missing front matter" in violation.message

    # Cleanup
    md_file.unlink()


def test_standardize_format_with_mixed_formats():
    # Arrange
    content = """---
title="Test Article"
description: A test article
date="2024-04-04"
tags: ["tag1", "tag2"]
categories: [cat1, cat2]
---
# Content here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    standardized_content = processor.standardize_format(md_file)

    # Assert
    expected_content = """---
title="Test Article"
description="A test article"
date="2024-04-04"
tags=["tag1", "tag2"]
categories=["cat1", "cat2"]
---
# Content here
"""
    assert standardized_content == expected_content

    # Cleanup
    md_file.unlink()


def test_standardize_format_with_already_standard_format():
    # Arrange
    content = """---
title="Test Article"
description="A test article"
date="2024-04-04"
---
# Content here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    standardized_content = processor.standardize_format(md_file)

    # Assert
    assert standardized_content == content

    # Cleanup
    md_file.unlink()


def test_standardize_format_with_missing_front_matter():
    # Arrange
    content = """# Just content
No front matter here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        processor.standardize_format(md_file)
    assert "Missing front matter" in str(exc_info.value)

    # Cleanup
    md_file.unlink()


def test_standardize_format_with_complex_values():
    # Arrange
    content = """---
title: "Article with: colon"
description: Article about \"quotes\" and stuff
date: 2024-04-04 15:30:00
list: [1, 2, 3]
nested: {key: value, other: stuff}
---
# Content here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    standardized_content = processor.standardize_format(md_file)

    # Assert
    expected_content = """---
title="Article with: colon"
description="Article about \\"quotes\\" and stuff"
date="2024-04-04 15:30:00"
list=[1, 2, 3]
nested={"key": "value", "other": "stuff"}
---
# Content here
"""
    assert standardized_content == expected_content

    # Cleanup
    md_file.unlink()


def test_remove_empty_lines():
    """Test empty line removal functionality in HugoProcessor."""
    config = {
        "source_dir": "test_source",
        "target_dir": "test_target",
        "image_dir": "test_images"
    }
    processor = HugoProcessor(config)
    content = (
        "---\n"
        "title=\"Test\"\n"
        "date=\"2024-04-04\"\n"
        "---\n"
        "\n"
        "\n"
        "First paragraph\n"
        "\n"
        "\n"
        "```python\n"
        "def test():\n"
        "\n"
        "    return None\n"
        "```\n"
        "\n"
        "\n"
        "- List item 1\n"
        "- List item 2\n"
        "\n"
        "- New group item\n"
        "\n"
        "\n"
        "Last paragraph"
    )
    expected = (
        "---\n"
        "title=\"Test\"\n"
        "date=\"2024-04-04\"\n"
        "---\n"
        "\n"
        "First paragraph\n"
        "\n"
        "```python\n"
        "def test():\n"
        "\n"
        "    return None\n"
        "```\n"
        "\n"
        "- List item 1\n"
        "- List item 2\n"
        "\n"
        "- New group item\n"
        "\n"
        "Last paragraph"
    )
    result = processor.remove_empty_lines(content)
    assert result == expected


def test_process_file_with_empty_lines():
    """Test that process_file handles empty lines correctly."""
    config = {
        "source_dir": "test_source",
        "target_dir": "test_target",
        "image_dir": "test_images"
    }
    processor = HugoProcessor(config)
    content = (
        "---\n"
        "title: Test\n"
        "date: 2024-04-04\n"
        "---\n"
        "\n"
        "\n"
        "Content with empty lines\n"
        "\n"
        "\n"
        "Should be standardized"
    )
    expected = (
        "---\n"
        "title=\"Test\"\n"
        "date=\"2024-04-04\"\n"
        "---\n"
        "\n"
        "Content with empty lines\n"
        "\n"
        "Should be standardized"
    )
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.md') as temp:
        temp.write(content)
        temp.flush()
        processor.process_file(temp.name)
        temp.seek(0)
        result = temp.read()
        assert result == expected


def test_publish_without_hugo_target_home():
    """Test publishing fails when HUGO_TARGET_HOME environment variable is not set."""
    # Arrange
    if "HUGO_TARGET_HOME" in os.environ:
        del os.environ["HUGO_TARGET_HOME"]

    processor = HugoProcessor({
        'source_dir': '/path/to/source',
        'target_dir': '/path/to/target',
        'image_dir': '/path/to/images'
    })

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        processor.publish()
    assert "HUGO_TARGET_HOME environment variable is not set" in str(
        exc_info.value)


def test_publish_with_invalid_hugo_target_home():
    """Test publishing fails when HUGO_TARGET_HOME points to non-existent directory."""
    # Arrange
    os.environ["HUGO_TARGET_HOME"] = "/non/existent/path"
    processor = HugoProcessor({
        'source_dir': '/path/to/source',
        'target_dir': '/path/to/target',
        'image_dir': '/path/to/images'
    })

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        processor.publish()
    assert "HUGO_TARGET_HOME directory does not exist" in str(exc_info.value)


def test_publish_with_valid_hugo_target_home():
    """Test publishing succeeds with valid HUGO_TARGET_HOME and creates required directories."""
    # Arrange
    with tempfile.TemporaryDirectory() as hugo_home:
        os.environ["HUGO_TARGET_HOME"] = hugo_home
        processor = HugoProcessor({
            'source_dir': '/path/to/source',
            'target_dir': '/path/to/target',
            'image_dir': '/path/to/images'
        })

        # Act
        processor.publish()

        # Assert
        blog_dir = Path(hugo_home) / "content" / "blog"
        img_dir = Path(hugo_home) / "static" / "img" / "blog"

        assert blog_dir.exists(), "Blog directory was not created"
        assert img_dir.exists(), "Image directory was not created"


def test_publish_copies_markdown_files():
    """Test that publish copies markdown files to the Hugo blog directory."""
    # Arrange
    with tempfile.TemporaryDirectory() as source_dir, \
            tempfile.TemporaryDirectory() as hugo_home:

        # Create test markdown files
        source_path = Path(source_dir)
        test_files = [
            "article1.md",
            "subfolder/article2.md",
            "deep/nested/article3.md"
        ]

        # Create the files with some content
        for file_path in test_files:
            full_path = source_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("""---
title="Test Article"
date="2024-04-04"
---
# Test content
""")

        # Set up HugoProcessor
        os.environ["HUGO_TARGET_HOME"] = hugo_home
        processor = HugoProcessor({
            'source_dir': str(source_path),
            'target_dir': '/tmp',  # Not used in this test
            'image_dir': '/tmp'    # Not used in this test
        })

        # Act
        processor.publish()

        # Assert
        hugo_blog_dir = Path(hugo_home) / "content" / "blog"
        for file_path in test_files:
            target_path = hugo_blog_dir / file_path
            assert target_path.exists(), f"File {file_path} was not copied"
            assert target_path.read_text() == (source_path / file_path).read_text(), \
                f"Content mismatch for {file_path}"


def test_publish_skips_non_markdown_files():
    """Test that publish only copies markdown files and skips others."""
    # Arrange
    with tempfile.TemporaryDirectory() as source_dir, \
            tempfile.TemporaryDirectory() as hugo_home:

        # Create test files
        source_path = Path(source_dir)
        markdown_file = source_path / "article.md"
        text_file = source_path / "notes.txt"
        json_file = source_path / "data.json"

        # Create the files with some content
        markdown_file.write_text("""---
title="Test Article"
date="2024-04-04"
---
# Test content
""")
        text_file.write_text("Some notes")
        json_file.write_text('{"key": "value"}')

        # Set up HugoProcessor
        os.environ["HUGO_TARGET_HOME"] = hugo_home
        processor = HugoProcessor({
            'source_dir': str(source_path),
            'target_dir': '/tmp',
            'image_dir': '/tmp'
        })

        # Act
        processor.publish()

        # Assert
        hugo_blog_dir = Path(hugo_home) / "content" / "blog"
        assert (hugo_blog_dir /
                "article.md").exists(), "Markdown file was not copied"
        assert not (hugo_blog_dir /
                    "notes.txt").exists(), "Text file was copied"
        assert not (hugo_blog_dir /
                    "data.json").exists(), "JSON file was copied"
