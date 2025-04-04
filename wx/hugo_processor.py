import logging
from pathlib import Path
from typing import Dict, Any


class HugoProcessor:
    """
    Processor for Hugo operations including format checking and publishing.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Hugo processor with configuration.

        Args:
            config: Dictionary containing:
                - source_dir: Source directory for markdown files
                - target_dir: Target directory for Hugo content
                - image_dir: Directory for storing images

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        self.config = self._validate_config(config)
        self.logger = logging.getLogger(__name__)

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the configuration dictionary.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validated configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        # Check required keys
        required_keys = ['source_dir', 'target_dir', 'image_dir']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"Missing required config keys: {missing_keys}")

        # Validate paths
        for key in required_keys:
            path = config[key]
            if not path:
                raise ValueError(f"Invalid path: {key} cannot be empty")

        return config
