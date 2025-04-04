import logging
import re
import json
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class FormatViolation:
    """Represents a format violation in a markdown file."""
    line_number: int
    message: str
    line_content: str = ""


class HugoProcessor:
    """
    Processor for Hugo operations including format checking and publishing.
    """

    # Front matter patterns
    FRONT_MATTER_START = "---"
    KEY_VALUE_PATTERN = re.compile(r'^(\w+)=["\'](.*)["\']$')
    KEY_COLON_PATTERN = re.compile(r'^(\w+):\s*(.*)$')

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

    def check_format(self, markdown_file: Path) -> List[FormatViolation]:
        """
        Check the format of a markdown file.

        Args:
            markdown_file: Path to the markdown file to check

        Returns:
            List of format violations found in the file
        """
        violations = []
        content = markdown_file.read_text()
        lines = content.splitlines()

        # Check for front matter
        if not content.startswith(self.FRONT_MATTER_START):
            return [FormatViolation(
                line_number=1,
                message="Missing front matter",
                line_content=lines[0] if lines else ""
            )]

        # Find front matter end
        front_matter_end = -1
        for i, line in enumerate(lines[1:], 1):
            if line == self.FRONT_MATTER_START:
                front_matter_end = i
                break

        if front_matter_end == -1:
            return [FormatViolation(
                line_number=1,
                message="Incomplete front matter: missing closing '---'",
                line_content=lines[0]
            )]

        # Check front matter format
        for i, line in enumerate(lines[1:front_matter_end], 1):
            line = line.strip()
            if not line:
                continue

            # Check if line uses key: value format
            if self.KEY_COLON_PATTERN.match(line):
                violations.append(FormatViolation(
                    line_number=i + 1,
                    message=f"Mixed format detected: '{line}' should use key=\"value\" format",
                    line_content=line
                ))
                continue

            # Check if line uses key="value" format
            if not self.KEY_VALUE_PATTERN.match(line):
                violations.append(FormatViolation(
                    line_number=i + 1,
                    message=f"Invalid format: '{line}' should use key=\"value\" format",
                    line_content=line
                ))

        return violations

    def standardize_format(self, markdown_file: Path) -> str:
        """
        Standardize the format of a markdown file to use key="value" format.

        Args:
            markdown_file: Path to the markdown file to standardize

        Returns:
            Standardized content as a string

        Raises:
            ValueError: If the file is missing front matter
        """
        content = markdown_file.read_text()
        if not content.endswith('\n'):
            content += '\n'
        lines = content.splitlines()

        # Check for front matter
        if not content.startswith(self.FRONT_MATTER_START):
            raise ValueError("Missing front matter")

        # Find front matter boundaries
        front_matter_end = -1
        for i, line in enumerate(lines[1:], 1):
            if line == self.FRONT_MATTER_START:
                front_matter_end = i
                break

        if front_matter_end == -1:
            raise ValueError("Incomplete front matter: missing closing '---'")

        # Process front matter
        standardized_lines = [self.FRONT_MATTER_START]
        for line in lines[1:front_matter_end]:
            line = line.strip()
            if not line:
                continue

            # Skip if already in key="value" format
            if self.KEY_VALUE_PATTERN.match(line):
                standardized_lines.append(line)
                continue

            # Convert key: value format
            if match := self.KEY_COLON_PATTERN.match(line):
                key, value = match.groups()
                standardized_value = self._standardize_value(value.strip())
                standardized_lines.append(f'{key}={standardized_value}')
                continue

            # Invalid format, keep as is but log warning
            self.logger.warning(f"Invalid front matter line format: {line}")
            standardized_lines.append(line)

        # Add closing front matter marker and remaining content
        standardized_lines.append(self.FRONT_MATTER_START)
        if front_matter_end + 1 < len(lines):
            standardized_lines.extend(lines[front_matter_end + 1:])

        return '\n'.join(standardized_lines) + '\n'

    def _standardize_value(self, value: str) -> str:
        """
        Standardize a front matter value to the key="value" format.

        Args:
            value: The value to standardize

        Returns:
            Standardized value string
        """
        # Remove surrounding quotes if present
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        # Handle JSON-like values (lists and objects)
        if value.startswith('[') or value.startswith('{'):
            try:
                # First try to parse with existing quotes
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    # If that fails, try replacing single quotes with double quotes
                    value = value.replace("'", '"')
                    # Handle unquoted list items
                    if value.startswith('['):
                        value = re.sub(r'\[([^"\]\[]*)\]', lambda m: '[' + ','.join(
                            f'"{x.strip()}"' for x in m.group(1).split(',')) + ']', value)
                    # Handle unquoted object keys and values
                    if value.startswith('{'):
                        value = re.sub(r'(\{|\,)\s*(\w+):', r'\1"\2":', value)
                        value = re.sub(r':\s*(\w+)([,\}])', r':"\1"\2', value)
                    parsed = json.loads(value)

                # For lists and objects, return the JSON string directly
                return json.dumps(parsed)
            except json.JSONDecodeError:
                # If parsing fails, treat as regular string
                pass

        # For simple values, escape quotes and wrap in double quotes
        value = value.replace('"', '\\"')
        return f'"{value}"'
