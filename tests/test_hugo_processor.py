import os
import tempfile
import pytest
from pathlib import Path
from typing import Dict, Any
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from wx.hugo_processor import HugoProcessor, FormatViolation


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


def create_temp_markdown_file(content: str) -> Path:
    """Helper function to create a temporary markdown file with given content."""
    temp_file = NamedTemporaryFile(delete=False, suffix='.md')
    temp_file.write(content.encode('utf-8'))
    temp_file.close()
    return Path(temp_file.name)


def test_check_format_with_consistent_key_value_format():
    # Arrange
    content = """---
title="Test Article"
description="A test article"
date="2024-04-04"
---
# Content here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    violations = processor.check_format(md_file)

    # Assert
    assert len(violations) == 0

    # Cleanup
    md_file.unlink()


def test_check_format_with_mixed_formats():
    # Arrange
    content = """---
title="Test Article"
description: A test article
date="2024-04-04"
---
# Content here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    violations = processor.check_format(md_file)

    # Assert
    assert len(violations) == 1
    violation = violations[0]
    assert isinstance(violation, FormatViolation)
    assert violation.line_number == 3  # The line with 'description: A test article'
    assert "Mixed format" in violation.message
    assert "description: A test article" in violation.message

    # Cleanup
    md_file.unlink()


def test_check_format_with_missing_front_matter():
    # Arrange
    content = """# Just content
No front matter here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    violations = processor.check_format(md_file)

    # Assert
    assert len(violations) == 1
    violation = violations[0]
    assert isinstance(violation, FormatViolation)
    assert violation.line_number == 1
    assert "Missing front matter" in violation.message

    # Cleanup
    md_file.unlink()


def test_standardize_format_with_mixed_formats():
    # Arrange
    content = """---
title="Test Article"
description: A test article
date="2024-04-04"
tags: ["tag1", "tag2"]
categories: [cat1, cat2]
---
# Content here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    standardized_content = processor.standardize_format(md_file)

    # Assert
    expected_content = """---
title="Test Article"
description="A test article"
date="2024-04-04"
tags=["tag1", "tag2"]
categories=["cat1", "cat2"]
---
# Content here
"""
    assert standardized_content == expected_content

    # Cleanup
    md_file.unlink()


def test_standardize_format_with_already_standard_format():
    # Arrange
    content = """---
title="Test Article"
description="A test article"
date="2024-04-04"
---
# Content here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    standardized_content = processor.standardize_format(md_file)

    # Assert
    assert standardized_content == content

    # Cleanup
    md_file.unlink()


def test_standardize_format_with_missing_front_matter():
    # Arrange
    content = """# Just content
No front matter here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        processor.standardize_format(md_file)
    assert "Missing front matter" in str(exc_info.value)

    # Cleanup
    md_file.unlink()


def test_standardize_format_with_complex_values():
    # Arrange
    content = """---
title: "Article with: colon"
description: Article about \"quotes\" and stuff
date: 2024-04-04 15:30:00
list: [1, 2, 3]
nested: {key: value, other: stuff}
---
# Content here
"""
    md_file = create_temp_markdown_file(content)
    processor = HugoProcessor(
        {'source_dir': str(md_file.parent), 'target_dir': '/tmp', 'image_dir': '/tmp'})

    # Act
    standardized_content = processor.standardize_format(md_file)

    # Assert
    expected_content = """---
title="Article with: colon"
description="Article about \\"quotes\\" and stuff"
date="2024-04-04 15:30:00"
list=[1, 2, 3]
nested={"key": "value", "other": "stuff"}
---
# Content here
"""
    assert standardized_content == expected_content

    # Cleanup
    md_file.unlink()


def test_remove_empty_lines():
    """Test empty line removal functionality in HugoProcessor."""
    config = {
        "source_dir": "test_source",
        "target_dir": "test_target",
        "image_dir": "test_images"
    }
    processor = HugoProcessor(config)
    content = (
        "---\n"
        "title=\"Test\"\n"
        "date=\"2024-04-04\"\n"
        "---\n"
        "\n"
        "\n"
        "First paragraph\n"
        "\n"
        "\n"
        "```python\n"
        "def test():\n"
        "\n"
        "    return None\n"
        "```\n"
        "\n"
        "\n"
        "- List item 1\n"
        "- List item 2\n"
        "\n"
        "- New group item\n"
        "\n"
        "\n"
        "Last paragraph"
    )
    expected = (
        "---\n"
        "title=\"Test\"\n"
        "date=\"2024-04-04\"\n"
        "---\n"
        "\n"
        "First paragraph\n"
        "\n"
        "```python\n"
        "def test():\n"
        "\n"
        "    return None\n"
        "```\n"
        "\n"
        "- List item 1\n"
        "- List item 2\n"
        "\n"
        "- New group item\n"
        "\n"
        "Last paragraph"
    )
    result = processor.remove_empty_lines(content)
    assert result == expected


def test_process_file_with_empty_lines():
    """Test that process_file handles empty lines correctly."""
    config = {
        "source_dir": "test_source",
        "target_dir": "test_target",
        "image_dir": "test_images"
    }
    processor = HugoProcessor(config)
    content = (
        "---\n"
        "title: Test\n"
        "date: 2024-04-04\n"
        "---\n"
        "\n"
        "\n"
        "Content with empty lines\n"
        "\n"
        "\n"
        "Should be standardized"
    )
    expected = (
        "---\n"
        "title=\"Test\"\n"
        "date=\"2024-04-04\"\n"
        "---\n"
        "\n"
        "Content with empty lines\n"
        "\n"
        "Should be standardized"
    )
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.md') as temp:
        temp.write(content)
        temp.flush()
        processor.process_file(temp.name)
        temp.seek(0)
        result = temp.read()
        assert result == expected


def test_publish_without_hugo_target_home():
    """Test publishing fails when HUGO_TARGET_HOME environment variable is not set."""
    # Arrange
    if "HUGO_TARGET_HOME" in os.environ:
        del os.environ["HUGO_TARGET_HOME"]

    processor = HugoProcessor({
        'source_dir': '/path/to/source',
        'target_dir': '/path/to/target',
        'image_dir': '/path/to/images'
    })

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        processor.publish()
    assert "HUGO_TARGET_HOME environment variable is not set" in str(
        exc_info.value)


def test_publish_with_invalid_hugo_target_home():
    """Test publishing fails when HUGO_TARGET_HOME points to non-existent directory."""
    # Arrange
    os.environ["HUGO_TARGET_HOME"] = "/non/existent/path"
    processor = HugoProcessor({
        'source_dir': '/path/to/source',
        'target_dir': '/path/to/target',
        'image_dir': '/path/to/images'
    })

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        processor.publish()
    assert "HUGO_TARGET_HOME directory does not exist" in str(exc_info.value)


def test_publish_with_valid_hugo_target_home():
    """Test publishing succeeds with valid HUGO_TARGET_HOME and creates required directories."""
    # Arrange
    with tempfile.TemporaryDirectory() as source_dir, \
            tempfile.TemporaryDirectory() as hugo_home:

        # Create a test markdown file
        source_path = Path(source_dir)
        test_file = source_path / "test.md"
        test_file.write_text("""---
title="Test Article"
date="2024-04-04"
---
# Test content
""")

        os.environ["HUGO_TARGET_HOME"] = hugo_home
        processor = HugoProcessor({
            'source_dir': source_dir,
            'target_dir': str(Path(hugo_home) / "content" / "blog"),
            'image_dir': str(Path(hugo_home) / "static" / "img" / "blog")
        })

        # Act
        result = processor.publish()

        # Assert
        assert result["success"] is True
        blog_dir = Path(hugo_home) / "content" / "blog"
        img_dir = Path(hugo_home) / "static" / "img" / "blog"

        assert blog_dir.exists(), "Blog directory was not created"
        assert img_dir.exists(), "Image directory was not created"
        assert (blog_dir / "test.md").exists(), "Markdown file was not copied"


def test_publish_copies_markdown_files():
    """Test that publish copies markdown files to the Hugo blog directory."""
    # Arrange
    with tempfile.TemporaryDirectory() as source_dir, \
            tempfile.TemporaryDirectory() as hugo_home:

        # Create test markdown files
        source_path = Path(source_dir)
        test_files = [
            "article1.md",
            "subfolder/article2.md",
            "deep/nested/article3.md"
        ]

        # Create the files with some content
        for file_path in test_files:
            full_path = source_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("""---
title="Test Article"
date="2024-04-04"
---
# Test content
""")

        # Set up HugoProcessor
        os.environ["HUGO_TARGET_HOME"] = hugo_home
        processor = HugoProcessor({
            'source_dir': str(source_path),
            'target_dir': '/tmp',  # Not used in this test
            'image_dir': '/tmp'    # Not used in this test
        })

        # Act
        processor.publish()

        # Assert
        hugo_blog_dir = Path(hugo_home) / "content" / "blog"
        for file_path in test_files:
            target_path = hugo_blog_dir / file_path
            assert target_path.exists(), f"File {file_path} was not copied"
            assert target_path.read_text() == (source_path / file_path).read_text(), \
                f"Content mismatch for {file_path}"


def test_publish_skips_non_markdown_files():
    """Test that publish only copies markdown files and skips others."""
    # Arrange
    with tempfile.TemporaryDirectory() as source_dir, \
            tempfile.TemporaryDirectory() as hugo_home:

        # Create test files
        source_path = Path(source_dir)
        markdown_file = source_path / "article.md"
        text_file = source_path / "notes.txt"
        json_file = source_path / "data.json"

        # Create the files with some content
        markdown_file.write_text("""---
title="Test Article"
date="2024-04-04"
---
# Test content
""")
        text_file.write_text("Some notes")
        json_file.write_text('{"key": "value"}')

        # Set up HugoProcessor
        os.environ["HUGO_TARGET_HOME"] = hugo_home
        processor = HugoProcessor({
            'source_dir': str(source_path),
            'target_dir': '/tmp',
            'image_dir': '/tmp'
        })

        # Act
        processor.publish()

        # Assert
        hugo_blog_dir = Path(hugo_home) / "content" / "blog"
        assert (hugo_blog_dir /
                "article.md").exists(), "Markdown file was not copied"
        assert not (hugo_blog_dir /
                    "notes.txt").exists(), "Text file was copied"
        assert not (hugo_blog_dir /
                    "data.json").exists(), "JSON file was copied"


def test_copy_image_files_basic(tmp_path):
    """Test basic image file copying functionality."""
    # Setup test environment
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    img_dir = source_dir / "images"
    img_dir.mkdir()

    # Create test image
    test_img = img_dir / "test.jpg"
    test_img.write_bytes(b"fake image content")

    # Create markdown file with image reference
    md_content = "![Test Image](images/test.jpg)"
    md_file = source_dir / "test.md"
    md_file.write_text(md_content)

    # Setup Hugo processor
    hugo_home = tmp_path / "hugo"
    hugo_home.mkdir()
    os.environ["HUGO_TARGET_HOME"] = str(hugo_home)

    config = {
        'source_dir': str(source_dir),
        'target_dir': str(hugo_home / "content" / "blog"),
        'image_dir': str(hugo_home / "static" / "img" / "blog")
    }
    processor = HugoProcessor(config)

    # Act
    image_mapping = processor.copy_image_files(md_file)

    # Assert
    expected_img_path = hugo_home / "static" / "img" / "blog" / "test.jpg"
    assert expected_img_path.exists()
    assert image_mapping == {"images/test.jpg": "/img/blog/test.jpg"}
    assert expected_img_path.read_bytes() == b"fake image content"


def test_copy_image_files_nested_structure(tmp_path):
    """Test copying images while maintaining directory structure."""
    # Setup test environment
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    nested_dir = source_dir / "posts" / "2024" / "images"
    nested_dir.mkdir(parents=True)

    # Create test image in nested directory
    test_img = nested_dir / "test.jpg"
    test_img.write_bytes(b"nested image content")

    # Create markdown file with image reference
    md_content = "![Nested Image](images/test.jpg)"
    md_file = source_dir / "posts" / "2024" / "article.md"
    md_file.parent.mkdir(parents=True, exist_ok=True)
    md_file.write_text(md_content)

    # Setup Hugo processor
    hugo_home = tmp_path / "hugo"
    hugo_home.mkdir()
    os.environ["HUGO_TARGET_HOME"] = str(hugo_home)

    config = {
        'source_dir': str(source_dir),
        'target_dir': str(hugo_home / "content" / "blog"),
        'image_dir': str(hugo_home / "static" / "img" / "blog")
    }
    processor = HugoProcessor(config)

    # Act
    image_mapping = processor.copy_image_files(md_file)

    # Assert
    expected_img_path = hugo_home / "static" / "img" / "blog" / "posts" / "test.jpg"
    assert expected_img_path.exists()
    assert image_mapping == {"images/test.jpg": "/img/blog/posts/test.jpg"}
    assert expected_img_path.read_bytes() == b"nested image content"


def test_copy_image_files_name_conflict(tmp_path):
    """Test handling of image file name conflicts."""
    # Setup test environment
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # Create two different images with the same name in different directories
    img_dir1 = source_dir / "post1" / "images"
    img_dir2 = source_dir / "post2" / "images"
    img_dir1.mkdir(parents=True)
    img_dir2.mkdir(parents=True)

    test_img1 = img_dir1 / "test.jpg"
    test_img2 = img_dir2 / "test.jpg"
    test_img1.write_bytes(b"image content 1")
    test_img2.write_bytes(b"image content 2")

    # Create markdown files referencing the images
    md_file1 = source_dir / "post1" / "article1.md"
    md_file2 = source_dir / "post2" / "article2.md"
    md_file1.write_text("![Test Image](images/test.jpg)")
    md_file2.write_text("![Test Image](images/test.jpg)")

    # Setup Hugo processor
    hugo_home = tmp_path / "hugo"
    hugo_home.mkdir()
    os.environ["HUGO_TARGET_HOME"] = str(hugo_home)

    config = {
        'source_dir': str(source_dir),
        'target_dir': str(hugo_home / "content" / "blog"),
        'image_dir': str(hugo_home / "static" / "img" / "blog")
    }
    processor = HugoProcessor(config)

    # Act
    image_mapping1 = processor.copy_image_files(md_file1)
    image_mapping2 = processor.copy_image_files(md_file2)

    # Assert
    img_dir = hugo_home / "static" / "img" / "blog"
    assert (img_dir / "post1" / "test.jpg").exists()
    assert (img_dir / "post2" / "test.jpg").exists()

    # Verify the content of both images was preserved
    img1_path = img_dir / "post1" / "test.jpg"
    img2_path = img_dir / "post2" / "test.jpg"
    assert img1_path.read_bytes() == b"image content 1"
    assert img2_path.read_bytes() == b"image content 2"

    # Verify the mappings
    assert image_mapping1 == {"images/test.jpg": "/img/blog/post1/test.jpg"}
    assert image_mapping2 == {"images/test.jpg": "/img/blog/post2/test.jpg"}


def test_update_image_references_basic(tmp_path):
    """Test basic image reference updating functionality."""
    # Setup
    content = """# Test Document
![Test Image](images/test.jpg)
Some text here
![Another Image](path/to/image.png)
"""
    path_mapping = {
        "images/test.jpg": "/img/blog/test.jpg",
        "path/to/image.png": "/img/blog/images/image.png"
    }

    # Create processor
    processor = HugoProcessor({
        'source_dir': str(tmp_path),
        'target_dir': str(tmp_path / "target"),
        'image_dir': str(tmp_path / "images")
    })

    # Act
    updated_content = processor.update_image_references(content, path_mapping)

    # Assert
    expected = """# Test Document
![Test Image](/img/blog/test.jpg)
Some text here
![Another Image](/img/blog/images/image.png)
"""
    assert updated_content == expected


def test_update_image_references_with_html(tmp_path):
    """Test updating HTML image references."""
    # Setup
    content = """# Test Document
<img src="images/test.jpg" alt="Test Image">
Some text here
<img src='path/to/image.png' alt='Another Image' class="large">
"""
    path_mapping = {
        "images/test.jpg": "/img/blog/test.jpg",
        "path/to/image.png": "/img/blog/images/image.png"
    }

    # Create processor
    processor = HugoProcessor({
        'source_dir': str(tmp_path),
        'target_dir': str(tmp_path / "target"),
        'image_dir': str(tmp_path / "images")
    })

    # Act
    updated_content = processor.update_image_references(content, path_mapping)

    # Assert
    expected = """# Test Document
<img src="/img/blog/test.jpg" alt="Test Image">
Some text here
<img src='/img/blog/images/image.png' alt='Another Image' class="large">
"""
    assert updated_content == expected


def test_update_image_references_mixed_format(tmp_path):
    """Test updating both Markdown and HTML image references."""
    # Setup
    content = """# Test Document
![Test Image](images/test.jpg)
Some text here
<img src="path/to/image.png" alt="Another Image">
More text
![Third Image](images/third.gif)
"""
    path_mapping = {
        "images/test.jpg": "/img/blog/test.jpg",
        "path/to/image.png": "/img/blog/images/image.png",
        "images/third.gif": "/img/blog/third.gif"
    }

    # Create processor
    processor = HugoProcessor({
        'source_dir': str(tmp_path),
        'target_dir': str(tmp_path / "target"),
        'image_dir': str(tmp_path / "images")
    })

    # Act
    updated_content = processor.update_image_references(content, path_mapping)

    # Assert
    expected = """# Test Document
![Test Image](/img/blog/test.jpg)
Some text here
<img src="/img/blog/images/image.png" alt="Another Image">
More text
![Third Image](/img/blog/third.gif)
"""
    assert updated_content == expected


def test_update_image_references_preserves_unmapped(tmp_path):
    """Test that unmapped image references are preserved as-is."""
    # Setup
    content = """# Test Document
![Test Image](images/test.jpg)
![Unmapped Image](images/unmapped.jpg)
<img src="path/to/unmapped.png" alt="Another Unmapped">
"""
    path_mapping = {
        "images/test.jpg": "/img/blog/test.jpg"
    }

    # Create processor
    processor = HugoProcessor({
        'source_dir': str(tmp_path),
        'target_dir': str(tmp_path / "target"),
        'image_dir': str(tmp_path / "images")
    })

    # Act
    updated_content = processor.update_image_references(content, path_mapping)

    # Assert
    expected = """# Test Document
![Test Image](/img/blog/test.jpg)
![Unmapped Image](images/unmapped.jpg)
<img src="path/to/unmapped.png" alt="Another Unmapped">
"""
    assert updated_content == expected


def test_publish_with_unwritable_hugo_target_home(tmp_path):
    """Test publishing fails when HUGO_TARGET_HOME directory is not writable."""
    # Arrange
    hugo_home = tmp_path / "hugo"
    hugo_home.mkdir()
    os.chmod(hugo_home, 0o444)  # Make directory read-only

    os.environ["HUGO_TARGET_HOME"] = str(hugo_home)
    processor = HugoProcessor({
        'source_dir': '/path/to/source',
        'target_dir': '/path/to/target',
        'image_dir': '/path/to/images'
    })

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        processor.publish()
    assert "HUGO_TARGET_HOME directory is not writable" in str(exc_info.value)

    # Cleanup
    os.chmod(hugo_home, 0o755)  # Restore permissions for cleanup


def test_publish_creates_required_directories():
    """Test that publish creates required Hugo directories if they don't exist."""
    # Arrange
    with tempfile.TemporaryDirectory() as hugo_home:
        os.environ["HUGO_TARGET_HOME"] = hugo_home
        processor = HugoProcessor({
            'source_dir': '/path/to/source',
            'target_dir': '/path/to/target',
            'image_dir': '/path/to/images'
        })

        # Act
        result = processor.validate_hugo_environment()

        # Assert
        blog_dir = Path(hugo_home) / "content" / "blog"
        img_dir = Path(hugo_home) / "static" / "img" / "blog"

        assert blog_dir.exists(), "Blog directory was not created"
        assert img_dir.exists(), "Image directory was not created"
        assert result is True, "Validation should return True when successful"


def test_publish_with_partial_directory_structure():
    """Test publishing with partially existing Hugo directory structure."""
    # Arrange
    with tempfile.TemporaryDirectory() as hugo_home:
        # Create only the content directory
        content_dir = Path(hugo_home) / "content"
        content_dir.mkdir()

        os.environ["HUGO_TARGET_HOME"] = hugo_home
        processor = HugoProcessor({
            'source_dir': '/path/to/source',
            'target_dir': '/path/to/target',
            'image_dir': '/path/to/images'
        })

        # Act
        result = processor.validate_hugo_environment()

        # Assert
        blog_dir = Path(hugo_home) / "content" / "blog"
        img_dir = Path(hugo_home) / "static" / "img" / "blog"

        assert blog_dir.exists(), "Blog directory was not created"
        assert img_dir.exists(), "Image directory was not created"
        assert result is True, "Validation should return True when successful"


def test_validate_hugo_environment_returns_false_on_error():
    """Test that validate_hugo_environment returns False when validation fails."""
    # Arrange
    if "HUGO_TARGET_HOME" in os.environ:
        del os.environ["HUGO_TARGET_HOME"]

    processor = HugoProcessor({
        'source_dir': '/path/to/source',
        'target_dir': '/path/to/target',
        'image_dir': '/path/to/images'
    })

    # Act
    result = processor.validate_hugo_environment()

    # Assert
    assert result is False, "Validation should return False when HUGO_TARGET_HOME is not set"


def test_copy_article_images(tmp_path):
    """Test copying article images to Hugo static directory.

    This test verifies:
    1. Images are correctly copied to the target directory
    2. Existing images are overwritten
    3. Directory structure is created if not exists
    """
    # Create test directory structure
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    images_dir = source_dir / "images"
    images_dir.mkdir()

    # Create test images
    test_image1 = images_dir / "test1.jpg"
    test_image1.write_bytes(b"test1 content")
    test_image2 = images_dir / "test2.png"
    test_image2.write_bytes(b"test2 content")

    # Create test markdown file with image references
    md_content = """+++
title="Test Article"
+++
# Test Article

![Test Image 1](images/test1.jpg)
![Test Image 2](images/test2.png)
"""
    md_file = source_dir / "test.md"
    md_file.write_text(md_content)

    # Set up Hugo target directory
    hugo_home = tmp_path / "hugo"
    hugo_home.mkdir()
    os.environ["HUGO_TARGET_HOME"] = str(hugo_home)

    # Initialize HugoProcessor
    processor = HugoProcessor({
        'source_dir': str(source_dir),
        'target_dir': str(hugo_home / "content" / "blog"),
        'image_dir': str(hugo_home / "static" / "img" / "blog")
    })

    # Create a file to be overwritten
    img_target_dir = hugo_home / "static" / "img" / "blog"
    img_target_dir.mkdir(parents=True)
    existing_image = img_target_dir / "test1.jpg"
    existing_image.write_bytes(b"old content")

    # Test image copying
    processor.copy_article_images(str(md_file))

    # Verify images were copied correctly
    copied_image1 = img_target_dir / "test1.jpg"
    copied_image2 = img_target_dir / "test2.png"

    assert copied_image1.exists(), "First image should be copied"
    assert copied_image2.exists(), "Second image should be copied"
    assert copied_image1.read_bytes() == b"test1 content", "First image should be overwritten"
    assert copied_image2.read_bytes() == b"test2 content", "Second image content should match"


def test_publish_result_notification(tmp_path):
    """Test that publish operation provides proper result notification"""
    # 创建测试目录结构
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "hugo_target"
    target_dir.mkdir()
    (target_dir / "content" / "blog").mkdir(parents=True)
    (target_dir / "static" / "img" / "blog").mkdir(parents=True)

    # 创建测试文件
    md_content = """+++
title="Test Article"
author="Test Author"
+++

# Test Article
![image1](images/test1.jpg)
![image2](images/test2.png)
"""
    md_file = source_dir / "test.md"
    md_file.write_text(md_content)

    # 创建图片目录和测试图片
    image_dir = source_dir / "images"
    image_dir.mkdir()
    (image_dir / "test1.jpg").write_bytes(b"fake jpg")
    (image_dir / "test2.png").write_bytes(b"fake png")

    # 设置环境变量和配置
    config = {
        'source_dir': str(source_dir),
        'target_dir': str(target_dir / "content" / "blog"),
        'image_dir': str(target_dir / "static" / "img" / "blog")
    }

    with patch.dict(os.environ, {'HUGO_TARGET_HOME': str(target_dir)}):
        processor = HugoProcessor(config)
        result = processor.publish([str(md_file)])

        # 验证结果格式
        assert isinstance(result, dict)
        assert "processed_files" in result
        assert "errors" in result

        # 验证处理的文件列表
        processed_files = result["processed_files"]
        assert len(processed_files) == 3  # 1 markdown + 2 images
        assert any(str(md_file) in f for f in processed_files)
        assert any("test1.jpg" in f for f in processed_files)
        assert any("test2.png" in f for f in processed_files)

        # 验证错误列表
        assert isinstance(result["errors"], list)
        assert len(result["errors"]) == 0  # 这个测试场景中应该没有错误


def test_publish_result_notification_with_errors(tmp_path):
    """Test that publish operation properly reports errors in the result"""
    # 创建测试目录结构
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "hugo_target"
    target_dir.mkdir()
    (target_dir / "content" / "blog").mkdir(parents=True)
    (target_dir / "static" / "img" / "blog").mkdir(parents=True)

    # 创建测试文件，引用不存在的图片
    md_content = """+++
title="Test Article"
author="Test Author"
+++

# Test Article
![missing](images/missing.jpg)
"""
    md_file = source_dir / "test.md"
    md_file.write_text(md_content)

    # 设置环境变量和配置
    config = {
        'source_dir': str(source_dir),
        'target_dir': str(target_dir / "content" / "blog"),
        'image_dir': str(target_dir / "static" / "img" / "blog")
    }

    with patch.dict(os.environ, {'HUGO_TARGET_HOME': str(target_dir)}):
        processor = HugoProcessor(config)
        result = processor.publish([str(md_file)])

        # 验证结果格式
        assert isinstance(result, dict)
        assert "processed_files" in result
        assert "errors" in result

        # 验证处理的文件列表
        processed_files = result["processed_files"]
        assert len(processed_files) == 1  # 只有 markdown 文件被处理
        assert any(str(md_file) in f for f in processed_files)

        # 验证错误列表
        assert isinstance(result["errors"], list)
        assert len(result["errors"]) > 0
        assert any("missing.jpg" in str(err) for err in result["errors"])


def test_validate_document_with_missing_images(tmp_path):
    # 准备测试目录
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    image_dir = tmp_path / "images"
    image_dir.mkdir()

    # 创建一个引用了不存在图片的 Markdown 文件
    md_content = """---
title="Test Article"
---
# Test Article

This is a test article with missing images:
![missing image](images/missing.jpg)
![another missing](images/not_found.png)
"""
    md_file = source_dir / "test.md"
    md_file.write_text(md_content)

    # 初始化 HugoProcessor
    config = {
        'source_dir': str(source_dir),
        'target_dir': str(target_dir),
        'image_dir': str(image_dir)
    }
    processor = HugoProcessor(config)

    # 验证文档
    validation_result = processor.validate_document(str(md_file))

    # 验证结果
    assert not validation_result.is_valid
    assert len(validation_result.missing_images) == 2
    assert "images/missing.jpg" in validation_result.missing_images
    assert "images/not_found.png" in validation_result.missing_images
    assert validation_result.error_messages
    assert "missing images" in validation_result.error_messages[0].lower()


def test_validate_document_with_incomplete_front_matter(tmp_path):
    # 准备测试目录
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    image_dir = tmp_path / "images"
    image_dir.mkdir()

    # 创建一个缺少必要 front matter 的 Markdown 文件
    md_content = """---
description="Test Description"
---
# Test Article

This is a test article.
"""
    md_file = source_dir / "test.md"
    md_file.write_text(md_content)

    # 初始化 HugoProcessor
    config = {
        'source_dir': str(source_dir),
        'target_dir': str(target_dir),
        'image_dir': str(image_dir)
    }
    processor = HugoProcessor(config)

    # 验证文档
    validation_result = processor.validate_document(str(md_file))

    # 验证结果
    assert not validation_result.is_valid
    assert len(validation_result.incomplete_front_matter) == 1
    assert "title" in validation_result.incomplete_front_matter
    assert validation_result.error_messages
    assert "missing required front matter" in validation_result.error_messages[0].lower(
    )


def test_validate_document_with_valid_content(tmp_path):
    # 准备测试目录
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    image_dir = tmp_path / "source/images"  # 修改图片目录位置
    image_dir.mkdir(parents=True)

    # 创建图片文件
    (image_dir / "test.jpg").touch()

    # 创建一个有效的 Markdown 文件
    md_content = """---
title="Test Article"
description="Test Description"
---
# Test Article

This is a test article with a valid image:
![test image](images/test.jpg)
"""
    md_file = source_dir / "test.md"
    md_file.write_text(md_content)

    # 初始化 HugoProcessor
    config = {
        'source_dir': str(source_dir),
        'target_dir': str(target_dir),
        'image_dir': str(image_dir)
    }
    processor = HugoProcessor(config)

    # 验证文档
    validation_result = processor.validate_document(str(md_file))

    # 验证结果
    assert validation_result.is_valid
    assert not validation_result.missing_images
    assert not validation_result.incomplete_front_matter
    assert not validation_result.error_messages


def test_publish_skips_invalid_documents(tmp_path, monkeypatch):
    # 准备测试目录
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    image_dir = tmp_path / "source/images"
    image_dir.mkdir(parents=True)
    hugo_dir = tmp_path / "hugo"
    hugo_dir.mkdir()

    # 设置 HUGO_TARGET_HOME 环境变量
    monkeypatch.setenv("HUGO_TARGET_HOME", str(hugo_dir))

    # 创建图片文件
    (image_dir / "valid.jpg").touch()

    # 创建一个有效的文档
    valid_content = """---
title="Valid Article"
description="Test Description"
---
# Valid Article

This is a valid article with an existing image:
![valid image](images/valid.jpg)
"""
    valid_file = source_dir / "valid.md"
    valid_file.write_text(valid_content)

    # 创建一个无效的文档（缺失图片）
    invalid_content = """---
title="Invalid Article"
description="Test Description"
---
# Invalid Article

This article has a missing image:
![missing image](images/missing.jpg)
"""
    invalid_file = source_dir / "invalid.md"
    invalid_file.write_text(invalid_content)

    # 初始化 HugoProcessor
    config = {
        'source_dir': str(source_dir),
        'target_dir': str(target_dir),
        'image_dir': str(image_dir)
    }
    processor = HugoProcessor(config)

    # 执行发布
    result = processor.publish([str(valid_file), str(invalid_file)])

    # 验证结果
    assert len(result["processed_files"]) == 1  # 只处理了有效文档
    assert str(valid_file) in result["processed_files"]
    assert len(result["skipped_files"]) == 1  # 跳过了无效文档
    assert str(invalid_file) in result["skipped_files"]
    assert any("missing images" in str(err) for err in result["errors"])

    # 验证文件是否正确复制到 Hugo 目录
    hugo_content_dir = hugo_dir / "content" / "blog"
    hugo_image_dir = hugo_dir / "static" / "img" / "blog"
    assert (hugo_content_dir / "valid.md").exists()
    assert (hugo_image_dir / "valid.jpg").exists()
    assert not (hugo_content_dir / "invalid.md").exists()
