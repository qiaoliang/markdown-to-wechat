import pytest
from pathlib import Path
from dataclasses import dataclass
from typing import List

from wx.image_reference import ImageReference, extract_image_references


def test_extract_markdown_image_references():
    """Test extracting standard markdown image references."""
    content = """
# Test Document

Here's an image: ![Alt text](path/to/image.jpg)

And another one: ![](images/photo.png)

With absolute path: ![Test](/absolute/path/pic.gif)
"""
    references = extract_image_references(content)

    assert len(references) == 3
    assert references[0] == ImageReference(
        original_text="![Alt text](path/to/image.jpg)",
        path="path/to/image.jpg",
        alt_text="Alt text",
        is_html=False
    )
    assert references[1] == ImageReference(
        original_text="![](images/photo.png)",
        path="images/photo.png",
        alt_text="",
        is_html=False
    )
    assert references[2] == ImageReference(
        original_text="![Test](/absolute/path/pic.gif)",
        path="/absolute/path/pic.gif",
        alt_text="Test",
        is_html=False
    )


def test_extract_html_image_references():
    """Test extracting HTML img tag references."""
    content = """
# Test Document

<img src="path/to/image.jpg" alt="Alt text">

<img src='/images/photo.png'>

<img src="/absolute/path/pic.gif" alt="Test" class="large">
"""
    references = extract_image_references(content)

    assert len(references) == 3
    assert references[0] == ImageReference(
        original_text='<img src="path/to/image.jpg" alt="Alt text">',
        path="path/to/image.jpg",
        alt_text="Alt text",
        is_html=True
    )
    assert references[1] == ImageReference(
        original_text="<img src='/images/photo.png'>",
        path="/images/photo.png",
        alt_text="",
        is_html=True
    )
    assert references[2] == ImageReference(
        original_text='<img src="/absolute/path/pic.gif" alt="Test" class="large">',
        path="/absolute/path/pic.gif",
        alt_text="Test",
        is_html=True
    )


def test_extract_mixed_image_references():
    """Test extracting both markdown and HTML image references."""
    content = """
# Test Document

![Markdown](image1.jpg)

<img src="image2.jpg" alt="HTML">

![](image3.jpg)
"""
    references = extract_image_references(content)

    assert len(references) == 3
    assert not references[0].is_html  # Markdown
    assert references[1].is_html      # HTML
    assert not references[2].is_html  # Markdown


def test_extract_no_image_references():
    """Test handling content with no image references."""
    content = """
# Test Document

Just some text without any images.

[A link](not/an/image.txt)
"""
    references = extract_image_references(content)
    assert len(references) == 0


def test_extract_invalid_image_references():
    """Test handling invalid image references."""
    content = """
# Test Document

![Bad markdown(image1.jpg)

<img src=>

![]()
"""
    references = extract_image_references(content)
    assert len(references) == 0
