import re
from dataclasses import dataclass
from typing import List


@dataclass
class ImageReference:
    """Represents an image reference in a markdown file."""
    original_text: str
    path: str
    alt_text: str
    is_html: bool


def extract_image_references(content: str) -> List[ImageReference]:
    """
    Extract all image references from markdown content.

    Args:
        content: The markdown content to process

    Returns:
        List of ImageReference objects containing details about each image reference
    """
    references = []

    # Extract HTML image references first (to avoid confusion with markdown)
    # Pattern: <img src="path" alt="alt text">
    # This pattern handles:
    # - Both single and double quotes
    # - Optional alt attribute
    # - Alt attribute before or after src
    # - Other attributes between src and alt
    # - Flexible whitespace
    html_pattern = r'<img\s+(?:[^>]*?\s+)?src=(["\'])(.*?)\1(?:\s+[^>]*?(?:alt=(["\'])(.*?)\3)?[^>]*)?>'
    for match in re.finditer(html_pattern, content):
        quote, path, alt_quote, alt_text = match.groups()
        if path:  # Only add if path is not empty
            references.append(ImageReference(
                original_text=match.group(0),
                path=path,
                alt_text=alt_text or "",  # Use empty string if alt_text is None
                is_html=True
            ))

    # Extract markdown image references
    # Pattern: ![alt text](path)
    markdown_pattern = r'!\[(.*?)\]\((.*?)\)'
    for match in re.finditer(markdown_pattern, content):
        alt_text, path = match.groups()
        if path:  # Only add if path is not empty
            # Check if this isn't part of an HTML tag
            start_pos = match.start()
            line_start = content.rfind('\n', 0, start_pos) + 1
            line = content[line_start:start_pos].strip()
            if not line.endswith('<'):  # Not part of an HTML tag
                references.append(ImageReference(
                    original_text=match.group(0),
                    path=path,
                    alt_text=alt_text,
                    is_html=False
                ))

    # Sort references by their appearance in the text
    references.sort(key=lambda r: content.find(r.original_text))

    return references
