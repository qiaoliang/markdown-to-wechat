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
