import logging
import re
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from .empty_line_processor import EmptyLineProcessor
from .image_reference import extract_image_references


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
        self.empty_line_processor = EmptyLineProcessor()

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

    def standardize_format(self, content: str | Path) -> str:
        """
        Standardize the format of markdown content to use key="value" format.

        Args:
            content: Either a Path to the markdown file or the content string

        Returns:
            Standardized content as a string

        Raises:
            ValueError: If the content is missing front matter
        """
        if isinstance(content, Path):
            content = content.read_text()

        # Extract front matter
        front_matter_match = re.match(
            r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if not front_matter_match:
            raise ValueError("Missing front matter in markdown file")

        front_matter = front_matter_match.group(1)
        rest_of_content = content[front_matter_match.end():]

        # Process front matter lines
        processed_lines = []
        for line in front_matter.splitlines():
            line = line.strip()
            if not line:
                continue

            # Skip lines that are already in key="value" format
            if re.match(r'^[^:=]+="[^"]*"$', line):
                processed_lines.append(line)
                continue

            # Convert key: value or key=value to key="value"
            match = re.match(r'^([^:=]+)[:=]\s*(.*)$', line)
            if match:
                key, value = match.groups()
                key = key.strip()
                value = value.strip()
                value = self._standardize_value(value)
                processed_lines.append(f'{key}={value}')

        # Reconstruct the content
        standardized_front_matter = "\n".join(processed_lines)
        return f"---\n{standardized_front_matter}\n---\n{rest_of_content}"

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

    def remove_empty_lines(self, content: str) -> str:
        """
        Remove unnecessary empty lines while preserving semantic structure.

        Args:
            content: The markdown content to process.

        Returns:
            The processed content with unnecessary empty lines removed.
        """
        return self.empty_line_processor.process_content(content)

    def process_file(self, file_path: str) -> None:
        """
        Process a markdown file for Hugo.

        This includes:
        1. Format standardization
        2. Empty line removal

        Args:
            file_path: Path to the markdown file to process.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # First standardize the format
        content = self.standardize_format(content)

        # Then remove unnecessary empty lines
        content = self.remove_empty_lines(content)

        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def publish(self) -> None:
        """
        Publish markdown files to Hugo site.

        This includes:
        1. Validating HUGO_TARGET_HOME environment variable
        2. Creating necessary directories
        3. Copying markdown files and images
        4. Updating image references

        Raises:
            ValueError: If HUGO_TARGET_HOME is not set or points to non-existent directory
        """
        # Validate HUGO_TARGET_HOME environment variable
        hugo_home = os.environ.get("HUGO_TARGET_HOME")
        if not hugo_home:
            raise ValueError(
                "HUGO_TARGET_HOME environment variable is not set")

        hugo_home_path = Path(hugo_home)
        if not hugo_home_path.exists():
            raise ValueError("HUGO_TARGET_HOME directory does not exist")

        # Create required directories
        blog_dir = hugo_home_path / "content" / "blog"
        img_dir = hugo_home_path / "static" / "img" / "blog"

        blog_dir.mkdir(parents=True, exist_ok=True)
        img_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Created Hugo directories: {blog_dir} and {img_dir}")

        # Copy markdown files
        source_path = Path(self.config['source_dir'])
        for file_path in source_path.rglob("*.md"):
            # Get relative path from source directory
            relative_path = file_path.relative_to(source_path)
            target_path = blog_dir / relative_path

            # Create parent directories if they don't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            target_path.write_text(file_path.read_text())
            self.logger.info(f"Copied {relative_path} to {target_path}")

    def copy_image_files(self, md_file: Path) -> Dict[str, str]:
        """
        Copy image files referenced in a markdown file to the Hugo static directory.

        Args:
            md_file: Path to the markdown file

        Returns:
            Dictionary mapping original image paths to new Hugo paths
        """
        # Read markdown content
        content = md_file.read_text()

        # Extract image references
        image_refs = extract_image_references(content)

        # Initialize path mapping
        path_mapping = {}

        # Get relative directory for nested structure
        relative_dir = md_file.parent.relative_to(
            Path(self.config['source_dir']))

        # Process each image reference
        for ref in image_refs:
            # Skip external images
            if not ref.path.startswith(('http://', 'https://')):
                # Resolve image path relative to markdown file
                img_path = (md_file.parent / ref.path).resolve()
                if img_path.exists():
                    # Create target directory if it doesn't exist
                    target_dir = Path(self.config['image_dir'])
                    if str(relative_dir) != '.':
                        # Use first directory level
                        target_dir = target_dir / \
                            str(relative_dir).split('/')[0]
                    target_dir.mkdir(parents=True, exist_ok=True)

                    # Generate unique filename if needed
                    base_name = img_path.stem
                    extension = img_path.suffix
                    target_path = target_dir / f"{base_name}{extension}"
                    counter = 1

                    while target_path.exists():
                        # If file exists but has same content, reuse it
                        if target_path.read_bytes() == img_path.read_bytes():
                            break
                        # Otherwise, create a new file with incremented counter
                        target_path = target_dir / \
                            f"{base_name}_{counter}{extension}"
                        counter += 1

                    # Copy the file
                    import shutil
                    shutil.copy2(img_path, target_path)

                    # Add to path mapping
                    relative_target = target_path.relative_to(
                        Path(self.config['image_dir']))
                    path_mapping[ref.path] = f"/img/blog/{relative_target}"

                    self.logger.info(
                        f"Copied image {img_path} to {target_path}")

        return path_mapping

    def update_image_references(self, content: str, path_mapping: Dict[str, str]) -> str:
        """
        Update image references in content based on the provided path mapping.

        Args:
            content: The markdown content containing image references
            path_mapping: Dictionary mapping original image paths to new Hugo paths

        Returns:
            Updated content with new image paths
        """
        # Update Markdown image references
        for old_path, new_path in path_mapping.items():
            # Escape special characters in the old path for regex
            escaped_old_path = re.escape(old_path)
            # Update Markdown format: ![alt](path)
            content = re.sub(
                f'!\\[([^\\]]*)\\]\\({escaped_old_path}\\)',
                f'![\\1]({new_path})',
                content
            )
            # Update HTML format with double quotes: <img src="path" ...>
            content = re.sub(
                f'<img([^>]*?)src="{escaped_old_path}"([^>]*?)>',
                f'<img\\1src="{new_path}"\\2>',
                content
            )
            # Update HTML format with single quotes: <img src='path' ...>
            content = re.sub(
                f"<img([^>]*?)src='{escaped_old_path}'([^>]*?)>",
                f"<img\\1src='{new_path}'\\2>",
                content
            )

        return content
