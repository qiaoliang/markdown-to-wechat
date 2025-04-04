import re
import requests
from pathlib import Path
from typing import Union
from urllib.parse import urlparse


class ImageProcessingError(Exception):
    """Base class for image processing errors."""
    pass


class ImageNotFoundError(ImageProcessingError):
    """Raised when an image file cannot be found."""
    pass


class InvalidImageReferenceError(ImageProcessingError):
    """Raised when an image reference is invalid."""
    pass


class NetworkImageError(ImageProcessingError):
    """Raised when there is an error downloading a network image."""
    pass


def validate_image_file(path: Path) -> None:
    """
    Validate that an image file exists and has a valid extension.

    Args:
        path: Path to the image file

    Raises:
        ImageNotFoundError: If the file does not exist
        InvalidImageReferenceError: If the file has an invalid extension
    """
    if not path.exists():
        raise ImageNotFoundError(f"Image file not found: {path}")

    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
    if path.suffix.lower() not in valid_extensions:
        raise InvalidImageReferenceError(
            f"Invalid image extension: {path.suffix}. "
            f"Supported extensions are: {', '.join(valid_extensions)}"
        )


def validate_image_reference(path: str) -> None:
    """
    Validate an image reference path or URL.

    Args:
        path: Image path or URL to validate

    Raises:
        InvalidImageReferenceError: If the path is empty or URL is invalid
    """
    if not path:
        raise InvalidImageReferenceError("Empty image path")

    # Check if it's a URL
    if path.startswith(('http://', 'https://')):
        parsed = urlparse(path)
        if not all([parsed.scheme, parsed.netloc]):
            raise InvalidImageReferenceError("Invalid image URL")


def download_network_image(url: str, target_dir: Union[str, Path]) -> Path:
    """
    Download an image from a URL.

    Args:
        url: URL of the image to download
        target_dir: Directory to save the downloaded image

    Returns:
        Path to the downloaded image

    Raises:
        NetworkImageError: If the download fails or content is invalid
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('content-type', '')

        # Get file extension from content type
        ext = None
        if 'image/jpeg' in content_type:
            ext = '.jpg'
        elif 'image/png' in content_type:
            ext = '.png'
        elif 'image/gif' in content_type:
            ext = '.gif'
        elif 'image/webp' in content_type:
            ext = '.webp'
        elif 'image/svg+xml' in content_type:
            ext = '.svg'

        # If content type doesn't indicate an image type, try to get extension from URL
        if not ext and not content_type.startswith('image/'):
            ext = Path(urlparse(url).path).suffix
            if not ext:
                raise NetworkImageError("Could not determine image extension")
            # Validate the extension from URL
            valid_extensions = {'.jpg', '.jpeg',
                                '.png', '.gif', '.webp', '.svg'}
            if ext.lower() not in valid_extensions:
                raise NetworkImageError(f"Invalid image extension: {ext}")

        # Create target directory
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        filename = re.sub(r'[^a-zA-Z0-9]', '_', url.split('/')[-1])
        target_path = target_dir / f"{filename}{ext}"

        # Save the image
        target_path.write_bytes(response.content)
        return target_path

    except requests.RequestException as e:
        raise NetworkImageError(f"Failed to download image: {str(e)}")
    except Exception as e:
        raise NetworkImageError(f"Error processing network image: {str(e)}")
