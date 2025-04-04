import pytest
from pathlib import Path
from typing import Dict, Any

from wx.hugo_processor import HugoProcessor


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
