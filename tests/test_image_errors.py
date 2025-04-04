import pytest
from pathlib import Path
from wx.image_errors import (
    ImageProcessingError,
    ImageNotFoundError,
    InvalidImageReferenceError,
    NetworkImageError,
    validate_image_file,
    validate_image_reference,
    download_network_image
)


def test_validate_image_file_not_found():
    """Test validation of non-existent image file."""
    with pytest.raises(ImageNotFoundError) as exc_info:
        validate_image_file(Path("/non/existent/image.jpg"))
    assert "Image file not found" in str(exc_info.value)


def test_validate_image_file_invalid_extension(tmp_path):
    """Test validation of file with invalid extension."""
    # Create a temporary text file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Not an image")

    with pytest.raises(InvalidImageReferenceError) as exc_info:
        validate_image_file(test_file)
    assert "Invalid image extension" in str(exc_info.value)


def test_validate_image_reference_empty_path():
    """Test validation of image reference with empty path."""
    with pytest.raises(InvalidImageReferenceError) as exc_info:
        validate_image_reference("")
    assert "Empty image path" in str(exc_info.value)


def test_validate_image_reference_invalid_url():
    """Test validation of image reference with invalid URL."""
    with pytest.raises(InvalidImageReferenceError) as exc_info:
        validate_image_reference("http://")
    assert "Invalid image URL" in str(exc_info.value)


def test_download_network_image_connection_error(tmp_path):
    """Test handling of network connection error during image download."""
    with pytest.raises(NetworkImageError) as exc_info:
        download_network_image(
            "http://non.existent.server/image.jpg", tmp_path)
    assert "Failed to download image" in str(exc_info.value)


def test_download_network_image_invalid_content(tmp_path, requests_mock):
    """Test handling of invalid content type during image download."""
    # Mock a response with non-image content type
    requests_mock.get(
        "http://example.com/not-an-image.txt",
        text="Not an image",
        headers={"content-type": "text/plain"}
    )

    with pytest.raises(NetworkImageError) as exc_info:
        download_network_image("http://example.com/not-an-image.txt", tmp_path)
    assert "Invalid image extension" in str(exc_info.value)


def test_download_network_image_jpeg(tmp_path, requests_mock):
    """Test successful download of JPEG image."""
    requests_mock.get(
        "http://example.com/image.jpg",
        content=b"fake-image-content",
        headers={"content-type": "image/jpeg"}
    )

    result = download_network_image("http://example.com/image.jpg", tmp_path)
    assert result.suffix == ".jpg"
    assert result.exists()
    assert result.read_bytes() == b"fake-image-content"


def test_download_network_image_png(tmp_path, requests_mock):
    """Test successful download of PNG image."""
    requests_mock.get(
        "http://example.com/image.png",
        content=b"fake-png-content",
        headers={"content-type": "image/png"}
    )

    result = download_network_image("http://example.com/image.png", tmp_path)
    assert result.suffix == ".png"
    assert result.exists()


def test_download_network_image_svg(tmp_path, requests_mock):
    """Test successful download of SVG image."""
    requests_mock.get(
        "http://example.com/image.svg",
        content=b"<svg></svg>",
        headers={"content-type": "image/svg+xml"}
    )

    result = download_network_image("http://example.com/image.svg", tmp_path)
    assert result.suffix == ".svg"
    assert result.exists()


def test_download_network_image_webp(tmp_path, requests_mock):
    """Test successful download of WebP image."""
    requests_mock.get(
        "http://example.com/image.webp",
        content=b"fake-webp-content",
        headers={"content-type": "image/webp"}
    )

    result = download_network_image("http://example.com/image.webp", tmp_path)
    assert result.suffix == ".webp"
    assert result.exists()


def test_download_network_image_gif(tmp_path, requests_mock):
    """Test successful download of GIF image."""
    requests_mock.get(
        "http://example.com/image.gif",
        content=b"fake-gif-content",
        headers={"content-type": "image/gif"}
    )

    result = download_network_image("http://example.com/image.gif", tmp_path)
    assert result.suffix == ".gif"
    assert result.exists()


def test_download_network_image_unknown_type_with_extension(tmp_path, requests_mock):
    """Test download with unknown content type but valid URL extension."""
    requests_mock.get(
        "http://example.com/image.jpg",
        content=b"fake-image-content",
        headers={"content-type": "application/octet-stream"}
    )

    result = download_network_image("http://example.com/image.jpg", tmp_path)
    assert result.suffix == ".jpg"
    assert result.exists()


def test_download_network_image_unknown_type_no_extension(tmp_path, requests_mock):
    """Test download with unknown content type and no extension."""
    requests_mock.get(
        "http://example.com/image",
        content=b"fake-image-content",
        headers={"content-type": "application/octet-stream"}
    )

    with pytest.raises(NetworkImageError) as exc_info:
        download_network_image("http://example.com/image", tmp_path)
    assert "Could not determine image extension" in str(exc_info.value)


def test_validate_image_reference_valid_url():
    """Test validation of valid image URL."""
    # Should not raise any exception
    validate_image_reference("https://example.com/image.jpg")


def test_validate_image_reference_local_path():
    """Test validation of local image path."""
    # Should not raise any exception
    validate_image_reference("/path/to/image.jpg")
