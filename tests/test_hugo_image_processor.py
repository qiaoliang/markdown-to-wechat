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
