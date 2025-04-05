class EmptyLineProcessor:
    """Process empty lines in Markdown content while preserving semantic structure."""

    def __init__(self):
        """Initialize the EmptyLineProcessor."""
        self.in_code_block = False
        self.in_front_matter = False
        self.code_block_marker = "```"
        self.front_matter_marker = "---"

    def is_code_block_delimiter(self, line: str) -> bool:
        """Check if the line is a code block delimiter."""
        return line.strip().startswith(self.code_block_marker)

    def is_front_matter_delimiter(self, line: str) -> bool:
        """Check if the line is a front matter delimiter."""
        return line.strip() == self.front_matter_marker

    def is_list_item(self, line: str) -> bool:
        """Check if the line is a list item."""
        stripped = line.strip()
        return (
            stripped.startswith("- ") or
            stripped.startswith("* ") or
            stripped.startswith("+ ") or
            (len(stripped) >
             1 and stripped[0].isdigit() and stripped[1] == ".")
        )

    def process_content(self, content: str) -> str:
        """
        Process the content and remove unnecessary empty lines.

        Args:
            content: The markdown content to process.

        Returns:
            The processed content with unnecessary empty lines removed.
            Always ends with a newline character.
        """
        if not content:
            return "\n"

        # Split content into lines, preserving line endings
        lines = content.splitlines(keepends=True)

        # Process middle content
        result = []
        prev_empty = False
        prev_list_item = False
        in_front_matter = False
        in_code_block = False

        for line in lines:
            is_empty = not line.strip()

            # Handle code blocks
            if self.is_code_block_delimiter(line):
                in_code_block = not in_code_block
                result.append(line)
                prev_empty = False
                continue

            # Handle front matter
            if self.is_front_matter_delimiter(line):
                in_front_matter = not in_front_matter
                result.append(line)
                prev_empty = False
                continue

            # Preserve content in code blocks and front matter
            if in_code_block or in_front_matter:
                result.append(line)
                continue

            is_list_item = self.is_list_item(line)

            # Handle empty lines
            if is_empty:
                # Skip consecutive empty lines
                if prev_empty:
                    continue
                # Keep empty line if it's between list groups
                if prev_list_item and not is_list_item:
                    result.append(line)
                    prev_empty = True
                    prev_list_item = False
                    continue
                # Keep single empty line between paragraphs
                result.append(line)
                prev_empty = True
            else:
                result.append(line)
                prev_empty = False

            prev_list_item = is_list_item

        # Ensure content ends with a single newline
        content = "".join(result)
        if not content.endswith("\n"):
            content += "\n"
        return content
