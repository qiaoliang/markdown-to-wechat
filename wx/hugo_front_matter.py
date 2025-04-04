import re
import ast
from typing import Dict, Any, List


class HugoFrontMatter:
    """Parser and validator for Hugo front matter."""

    REQUIRED_FIELDS = ["title"]
    OPTIONAL_FIELDS = ["subtitle", "description",
                       "tags", "banner", "categories", "keywords"]

    def __init__(self, content: str):
        """Initialize with markdown content containing front matter.

        Args:
            content: The full markdown content including front matter
        """
        self.raw_content = content
        self.front_matter: Dict[str, Any] = {}
        self._content: str = ""

    def parse(self) -> Dict[str, Any]:
        """Parse the front matter from the content.

        Returns:
            Dict containing the parsed front matter fields
        """
        # Split content at the first '---' marker
        parts = self.raw_content.split("---", 1)
        if len(parts) < 2:
            raise ValueError("No front matter found in content")

        front_matter_raw = parts[0]
        self._content = parts[1] if len(parts) > 1 else ""

        # Parse each line of front matter
        for line in front_matter_raw.strip().split("\n"):
            if not line.strip():
                continue

            # Try key="value" format
            key_value_match = re.match(r'^(\w+)="(.*)"$', line)
            if key_value_match:
                key, value = key_value_match.groups()
                self.front_matter[key] = self._parse_value(value)
                continue

            # Try key=value format (for lists)
            key_list_match = re.match(r'^(\w+)=(\[.*\])$', line)
            if key_list_match:
                key, value = key_list_match.groups()
                self.front_matter[key] = self._parse_list(value)
                continue

            # Try key: value format
            key_colon_match = re.match(r'^(\w+):\s*(.*)$', line)
            if key_colon_match:
                key, value = key_colon_match.groups()
                if value.startswith("[") and value.endswith("]"):
                    self.front_matter[key] = self._parse_list(value)
                else:
                    self.front_matter[key] = self._parse_value(value)

        return self.front_matter

    def _parse_value(self, value: str) -> Any:
        """Parse a front matter value."""
        return value.strip('"')  # Remove quotes if present

    def _parse_list(self, value: str) -> List[str]:
        """Parse a list value from front matter."""
        try:
            # Use ast.literal_eval for safe evaluation of list literals
            result = ast.literal_eval(value)
            if isinstance(result, list):
                return result
        except:
            pass
        # Handle invalid list format by splitting on commas and spaces
        items = []
        for item in value.strip("[]").split():
            item = item.strip().strip(",")
            if item:
                items.append(item)
        return items

    def validate(self) -> None:
        """Validate that all required fields are present.

        Raises:
            ValueError: If any required field is missing
        """
        for field in self.REQUIRED_FIELDS:
            if field not in self.front_matter:
                raise ValueError(f"Missing required field: {field}")

    def to_string(self) -> str:
        """Convert the front matter back to string format using key="value" format.

        Returns:
            String representation of the front matter
        """
        lines = []
        for key, value in self.front_matter.items():
            if isinstance(value, list):
                # Format lists with proper string representation
                list_str = [f'"{item}"' if isinstance(
                    item, str) else str(item) for item in value]
                lines.append(f'{key}=[{", ".join(list_str)}]')
            else:
                lines.append(f'{key}="{value}"')
        return "\n".join(lines)

    def get_content(self) -> str:
        """Get the content without front matter.

        Returns:
            The markdown content without front matter
        """
        return self._content.strip()
