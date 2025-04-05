import logging
import re
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from .empty_line_processor import EmptyLineProcessor
from .hugo_image_processor import HugoImageProcessor


@dataclass
class FormatViolation:
    """Represents a format violation in a markdown file."""
    line_number: int
    message: str
    line_content: str = ""


@dataclass
class ValidationResult:
    """存储文档验证的结果"""
    is_valid: bool = True
    missing_images: List[str] = field(default_factory=list)
    incomplete_front_matter: List[str] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)


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
        self.image_processor = HugoImageProcessor(
            self.config['source_dir'],
            self.config['image_dir']
        )

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

    def validate_hugo_environment(self) -> None:
        """
        Validate the Hugo environment and create required directories if they don't exist.

        This method checks:
        1. HUGO_TARGET_HOME environment variable exists
        2. The directory exists and is writable
        3. Required subdirectories exist or can be created

        Raises:
            ValueError: If environment validation fails for any reason
        """
        # Check HUGO_TARGET_HOME environment variable
        hugo_home = os.environ.get("HUGO_TARGET_HOME")
        if not hugo_home:
            raise ValueError(
                "HUGO_TARGET_HOME environment variable is not set")

        hugo_path = Path(hugo_home)
        if not hugo_path.exists():
            raise ValueError("HUGO_TARGET_HOME directory does not exist")

        # Check if directory is writable by attempting to create a temporary file
        try:
            test_file = hugo_path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError):
            raise ValueError("HUGO_TARGET_HOME directory is not writable")

        # Create required directories
        blog_dir = hugo_path / "content" / "blog"
        img_dir = hugo_path / "static" / "img" / "blog"

        try:
            blog_dir.mkdir(parents=True, exist_ok=True)
            img_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise ValueError(f"Failed to create required directories: {e}")

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
            r'^---\s*(.*?)\s*---\s*', content, re.DOTALL)
        if not front_matter_match:
            # If no front matter is found, add a minimal one
            return f"---\ntitle=\"Untitled\"\n---\n{content}"

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

        # Ensure title is present
        if not any(line.startswith('title=') for line in processed_lines):
            processed_lines.insert(0, 'title="Untitled"')

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

    def process_file(self, file_path: str) -> str:
        """
        Process a markdown file for Hugo.

        This includes:
        1. Format standardization
        2. Empty line removal

        Args:
            file_path: Path to the markdown file to process.

        Returns:
            The processed content as a string.
        """
        # 读取源文件内容
        md_file = Path(file_path)
        with md_file.open('r', encoding='utf-8') as f:
            content = f.read()

        # 标准化格式
        content = self.standardize_format(content)

        # 移除不必要的空行
        content = self.remove_empty_lines(content)

        return content

    def _copy_to_hugo_directory(self, file_path: str | Path, content: str) -> None:
        """
        Copy the processed markdown file to Hugo directory.

        Args:
            file_path: Path to the source markdown file.
            content: The processed content to write.

        Raises:
            ValueError: If HUGO_TARGET_HOME is not set or invalid.
        """
        # Get target path
        source_path = Path(self.config['source_dir'])
        md_path = Path(file_path)
        try:
            rel_path = md_path.relative_to(source_path)
        except ValueError:
            # If file is not in source directory, use file name
            rel_path = md_path.name

        # Build target path
        hugo_home = os.environ.get("HUGO_TARGET_HOME")
        if not hugo_home:
            raise ValueError(
                "HUGO_TARGET_HOME environment variable is not set")

        hugo_path = Path(hugo_home)
        if not hugo_path.exists():
            raise ValueError("HUGO_TARGET_HOME directory does not exist")

        # Check if directory is writable
        try:
            test_file = hugo_path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError):
            raise ValueError("HUGO_TARGET_HOME directory is not writable")

        target_file = hugo_path / "content" / "blog" / rel_path
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Write target file
        target_file.write_text(content)

    def publish(self, files: List[str | Path] | None = None) -> Dict[str, Any]:
        """
        Publish markdown files to Hugo directory.

        Args:
            files: List of markdown files to publish. If None, process all markdown files in source directory.

        Returns:
            Dict containing:
            - processed_files: List of successfully processed files
            - skipped_files: List of skipped files with reasons
            - errors: List of errors encountered
            - overwritten_files: List of files that were overwritten
            - success: Boolean indicating overall success

        Raises:
            ValueError: If Hugo environment validation fails
        """
        result = {
            "processed_files": [],
            "skipped_files": [],
            "errors": [],
            "overwritten_files": [],
            "success": True
        }

        # Validate Hugo environment first
        try:
            self.validate_hugo_environment()
        except ValueError as e:
            # Re-raise environment validation errors
            raise

        try:
            # Get list of files to process
            if files is None:
                source_path = Path(self.config['source_dir'])
                files = list(source_path.glob('**/*.md'))
            else:
                files = [Path(f) for f in files]

            # Process each file
            for file_path in files:
                try:
                    # Validate document
                    validation_result = self.validate_document(str(file_path))
                    if not validation_result.is_valid:
                        result["skipped_files"].append({
                            "file": str(file_path),
                            "reason": " | ".join(validation_result.error_messages)
                        })
                        result["errors"].extend(
                            validation_result.error_messages)
                        continue

                    # Process the file
                    processed_content = self.process_file(str(file_path))

                    # Copy images and update references
                    image_mapping = self.copy_article_images(file_path)
                    if image_mapping:
                        processed_content = self.update_image_references(
                            processed_content, image_mapping)

                    # Check if files will be overwritten
                    hugo_home = Path(os.environ["HUGO_TARGET_HOME"])
                    target_md_path = hugo_home / "content" / "blog" / file_path.name
                    if target_md_path.exists():
                        result["overwritten_files"].append(str(target_md_path))

                    # Copy processed content to Hugo directory
                    self._copy_to_hugo_directory(file_path, processed_content)
                    result["processed_files"].append(str(file_path))

                    # Add processed images to the list
                    for img_path in image_mapping.keys():
                        img_full_path = file_path.parent / img_path
                        result["processed_files"].append(str(img_full_path))
                        target_img_path = hugo_home / "static" / "img" / "blog" / img_full_path.name
                        if target_img_path.exists():
                            result["overwritten_files"].append(
                                str(target_img_path))

                except Exception as e:
                    error_msg = f"Error processing {file_path}: {str(e)}"
                    result["errors"].append(error_msg)
                    result["skipped_files"].append({
                        "file": str(file_path),
                        "reason": error_msg
                    })

        except Exception as e:
            result["errors"].append(f"Global error: {str(e)}")
            result["success"] = False

        # Set overall success status
        if result["errors"] or result["skipped_files"]:
            result["success"] = False

        return result

    def copy_image_files(self, md_file: Path) -> Dict[str, str]:
        """
        Copy image files referenced in a markdown file to the Hugo static directory.

        Args:
            md_file: Path to the markdown file

        Returns:
            Dictionary mapping original image paths to new Hugo paths
        """
        image_mapping = {}

        # Get all image references from the markdown file
        content = md_file.read_text()
        image_refs = self.image_processor.extract_image_references(content)
        if not image_refs:
            return image_mapping

        # Get source directory path and markdown file's relative path
        source_path = Path(self.config['source_dir'])
        try:
            md_rel_dir = md_file.parent.relative_to(source_path)
        except ValueError:
            # If the markdown file is not under source_path, return empty mapping
            return image_mapping

        # Prepare target directory base
        hugo_home = os.environ.get("HUGO_TARGET_HOME")
        if not hugo_home:
            return image_mapping

        # Process each image reference
        for img_ref in image_refs:
            # Skip external images
            if img_ref.path.startswith(('http://', 'https://')):
                continue

            # Resolve image path relative to markdown file
            img_path = md_file.parent / img_ref.path
            if not img_path.exists():
                continue

            # Create target directory structure based on markdown file's location
            target_img_dir = Path(hugo_home) / "static" / "img" / "blog"
            if str(md_rel_dir) != '.':
                # Only use the first directory level
                target_img_dir = target_img_dir / md_rel_dir.parts[0]
            target_img_dir.mkdir(parents=True, exist_ok=True)

            # Prepare target file name
            target_name = img_path.name
            target_path = target_img_dir / target_name

            # Handle name conflicts
            counter = 1
            while target_path.exists():
                # If files are identical, reuse the existing file
                if target_path.read_bytes() == img_path.read_bytes():
                    break

                # Otherwise, create a new name
                name_parts = target_name.rsplit('.', 1)
                if len(name_parts) > 1:
                    target_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                else:
                    target_name = f"{name_parts[0]}_{counter}"
                target_path = target_img_dir / target_name
                counter += 1

            # Copy the image file
            target_path.write_bytes(img_path.read_bytes())
            self.logger.info(f"Copied image {img_path} to {target_path}")

            # Update the mapping with paths relative to Hugo root
            original_path = img_ref.path
            if str(md_rel_dir) == '.':
                new_path = f"/img/blog/{target_name}"
            else:
                new_path = f"/img/blog/{md_rel_dir.parts[0]}/{target_name}"
            image_mapping[original_path] = new_path

        return image_mapping

    def update_image_references(self, content: str, path_mapping: Dict[str, str]) -> str:
        """
        Update image references in content based on the provided path mapping.

        Args:
            content: The markdown content containing image references
            path_mapping: Dictionary mapping original image paths to new Hugo paths

        Returns:
            Updated content with new image paths
        """
        return self.image_processor.update_image_references(content, path_mapping)

    def process_directory(self, directory: str) -> Dict[str, Any]:
        """
        Process all markdown files in a directory for Hugo.

        Args:
            directory: Path to the directory containing markdown files

        Returns:
            Dictionary containing:
                - success: bool indicating if all operations were successful
                - processed_files: list of processed file paths
                - errors: list of errors encountered
        """
        result = {
            "success": True,
            "processed_files": [],
            "errors": []
        }

        try:
            source_path = Path(directory)
            if not source_path.exists():
                raise ValueError(f"Directory does not exist: {directory}")

            # Process all markdown files in the directory and subdirectories
            for md_file in source_path.rglob("*.md"):
                try:
                    # Check format first
                    violations = self.check_format(md_file)
                    if violations:
                        result["errors"].append({
                            "file": str(md_file),
                            "violations": violations
                        })
                        continue

                    # Process the file
                    self.process_file(str(md_file))
                    result["processed_files"].append(str(md_file))
                except Exception as e:
                    result["errors"].append({
                        "file": str(md_file),
                        "error": str(e)
                    })
                    result["success"] = False

        except Exception as e:
            result["errors"].append({
                "error": str(e)
            })
            result["success"] = False

        return result

    def copy_article_images(self, md_file: str | Path) -> Dict[str, str]:
        """
        Copy images referenced in a markdown file to the Hugo static directory.
        If target images already exist, they will be overwritten.

        Args:
            md_file: Path to the markdown file

        Returns:
            Dictionary mapping original image paths to new Hugo paths
        """
        image_mapping = {}

        # Get all image references from the markdown file
        md_path = Path(md_file)
        content = md_path.read_text()

        # Get all image references from the markdown file
        image_refs = self.image_processor.extract_image_references(content)
        if not image_refs:
            return image_mapping

        # Get source directory path and markdown file's relative path
        source_path = Path(self.config['source_dir'])
        try:
            md_rel_dir = md_path.parent.relative_to(source_path)
        except ValueError:
            # If the markdown file is not under source_path, return empty mapping
            return image_mapping

        # Prepare target directory base
        hugo_home = os.environ.get("HUGO_TARGET_HOME")
        if not hugo_home:
            return image_mapping

        hugo_path = Path(hugo_home)
        # Process each image reference
        for img_ref in image_refs:
            # Skip external images
            if img_ref.path.startswith(('http://', 'https://')):
                continue

            # Resolve image path relative to markdown file
            img_path = md_path.parent / img_ref.path
            if not img_path.exists():
                continue

            # Create target directory structure based on markdown file's location
            target_img_dir = hugo_path / "static" / "img" / "blog"
            if str(md_rel_dir) != '.':
                # Only use the first directory level
                target_img_dir = target_img_dir / md_rel_dir.parts[0]
            target_img_dir.mkdir(parents=True, exist_ok=True)

            # Prepare target file name and path
            target_name = img_path.name
            target_path = target_img_dir / target_name

            # Copy the image file (always overwrite)
            target_path.write_bytes(img_path.read_bytes())

            # Update the mapping with paths relative to Hugo root
            if str(md_rel_dir) == '.':
                new_path = f"/img/blog/{target_name}"
            else:
                new_path = f"/img/blog/{md_rel_dir.parts[0]}/{target_name}"
            image_mapping[img_ref.path] = new_path

        return image_mapping

    def validate_document(self, file_path: str) -> ValidationResult:
        """验证单个 Markdown 文档的格式

        Args:
            file_path: Markdown 文件路径

        Returns:
            ValidationResult: 包含验证结果的对象
        """
        result = ValidationResult()

        try:
            content = Path(file_path).read_text()

            # 检查图片引用
            image_refs = self.image_processor.extract_image_references(content)
            for ref in image_refs:
                img_path = Path(file_path).parent / ref.path
                if not img_path.exists():
                    result.missing_images.append(ref.path)

            if result.missing_images:
                result.is_valid = False
                result.error_messages.append(
                    f"Document contains missing images: {', '.join(result.missing_images)}")

            # 检查 front matter
            required_front_matter = ['title']  # 可以根据需要添加更多必需字段

            # 提取 front matter
            if content.startswith(self.FRONT_MATTER_START):
                lines = content.splitlines()
                front_matter_end = -1
                for i, line in enumerate(lines[1:], 1):
                    if line == self.FRONT_MATTER_START:
                        front_matter_end = i
                        break

                if front_matter_end != -1:
                    front_matter_lines = lines[1:front_matter_end]
                    found_keys = set()

                    for line in front_matter_lines:
                        line = line.strip()
                        if not line:
                            continue

                        # 检查两种格式
                        key_value_match = self.KEY_VALUE_PATTERN.match(line)
                        key_colon_match = self.KEY_COLON_PATTERN.match(line)

                        if key_value_match:
                            found_keys.add(key_value_match.group(1))
                        elif key_colon_match:
                            found_keys.add(key_colon_match.group(1))

                    # 检查必需字段
                    missing_keys = [
                        key for key in required_front_matter if key not in found_keys]
                    if missing_keys:
                        result.is_valid = False
                        result.incomplete_front_matter.extend(missing_keys)
                        result.error_messages.append(
                            f"Missing required front matter fields: {', '.join(missing_keys)}")
                else:
                    result.is_valid = False
                    result.error_messages.append(
                        "Invalid front matter: missing closing '---'")
            else:
                result.is_valid = False
                result.error_messages.append("Missing front matter")

        except Exception as e:
            result.is_valid = False
            result.error_messages.append(
                f"Error validating document: {str(e)}")

        return result
