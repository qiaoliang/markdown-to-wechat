import pytest
from pathlib import Path
from wx.hugo_image_processor import HugoImageProcessor


def test_hugo_image_processor_initialization():
    source_dir = Path("/test/source")
    target_dir = Path("/test/target")
    processor = HugoImageProcessor(source_dir, target_dir)

    assert processor.source_dir == source_dir
    assert processor.target_dir == target_dir


def test_process_image_path_converts_to_hugo_format():
    source_dir = Path("/test/source")
    target_dir = Path("/test/target")
    processor = HugoImageProcessor(source_dir, target_dir)

    # Test relative path
    assert processor.process_image_path(
        "images/test.png") == "/img/blog/test.png"

    # Test absolute path
    assert processor.process_image_path(
        "/test/source/images/test.png") == "/img/blog/test.png"


def test_get_target_image_path():
    source_dir = Path("/test/source")
    target_dir = Path("/test/target")
    processor = HugoImageProcessor(source_dir, target_dir)

    source_image = Path("/test/source/images/test.png")
    expected_target = Path("/test/target/test.png")

    assert processor.get_target_image_path(source_image) == expected_target


def test_copy_image(tmp_path):
    # Setup test directories
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()

    # Create a test image file
    test_image = source_dir / "test.png"
    test_image.write_bytes(b"test image content")

    processor = HugoImageProcessor(source_dir, target_dir)
    target_path = processor.copy_image(test_image)

    assert target_path.exists()
    assert target_path.read_bytes() == b"test image content"


def test_extract_image_references():
    source_dir = Path("/test/source")
    target_dir = Path("/test/target")
    processor = HugoImageProcessor(source_dir, target_dir)

    content = """# Test Document
![Test Image](images/test.jpg)
Some text here
<img src="path/to/image.png" alt="Another Image">
"""
    refs = processor.extract_image_references(content)

    assert len(refs) == 2
    assert refs[0].path == "images/test.jpg"
    assert refs[0].alt_text == "Test Image"
    assert not refs[0].is_html
    assert refs[1].path == "path/to/image.png"
    assert refs[1].alt_text == "Another Image"
    assert refs[1].is_html


def test_update_image_references():
    source_dir = Path("/test/source")
    target_dir = Path("/test/target")
    processor = HugoImageProcessor(source_dir, target_dir)

    content = """# Test Document
![Test Image](images/test.jpg)
Some text here
<img src="path/to/image.png" alt="Another Image">
"""
    path_mapping = {
        "images/test.jpg": "/img/blog/test.jpg",
        "path/to/image.png": "/img/blog/image.png"
    }

    updated_content = processor.update_image_references(content, path_mapping)

    assert "![Test Image](/img/blog/test.jpg)" in updated_content
    assert '<img src="/img/blog/image.png" alt="Another Image">' in updated_content


def test_copy_article_images(tmp_path):
    # Setup test directories
    source_dir = tmp_path / "source"
    images_dir = source_dir / "images"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    images_dir.mkdir()
    target_dir.mkdir()

    # Create test images
    test_image1 = images_dir / "test1.jpg"
    test_image2 = images_dir / "test2.png"
    test_image1.write_bytes(b"test image 1")
    test_image2.write_bytes(b"test image 2")

    # Create test markdown file
    md_content = """# Test Document
![Test Image 1](images/test1.jpg)
Some text here
<img src="images/test2.png" alt="Test Image 2">
"""
    md_file = source_dir / "test.md"
    md_file.write_text(md_content)

    # Process images
    processor = HugoImageProcessor(source_dir, target_dir)
    path_mapping = processor.copy_article_images(md_file)

    # Verify path mapping
    assert path_mapping["images/test1.jpg"] == "/img/blog/test1.jpg"
    assert path_mapping["images/test2.png"] == "/img/blog/test2.png"

    # Verify files were copied
    assert (target_dir / "test1.jpg").exists()
    assert (target_dir / "test2.png").exists()
    assert (target_dir / "test1.jpg").read_bytes() == b"test image 1"
    assert (target_dir / "test2.png").read_bytes() == b"test image 2"
