class EmptyLineProcessor:
    """Process empty lines in Markdown content while preserving semantic structure."""

    def process_content(self, content: str) -> str:
        """
        Process the content and remove unnecessary empty lines.

        Args:
            content: The markdown content to process.

        Returns:
            The processed content with unnecessary empty lines removed.
        """
        if not content:
            return ""

        # Split content into lines, preserving line endings
        lines = content.splitlines(keepends=True)

        # Remove empty lines at the start and end
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        if not lines:
            return ""

        # Process middle content
        result = []
        prev_empty = False

        for line in lines:
            is_empty = not line.strip()

            # Skip consecutive empty lines
            if is_empty and prev_empty:
                continue

            result.append(line)
            prev_empty = is_empty

        return "".join(result)
