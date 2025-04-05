from pathlib import Path
import shutil


class HugoImageProcessor:
    """
    Handles image processing operations for Hugo content.
    Responsible for:
    - Converting image paths to Hugo format
    - Copying images to Hugo static directory
    - Managing image path transformations
    """

    def __init__(self, source_dir: Path | str, target_dir: Path | str):
        """
        Initialize the Hugo image processor.

        Args:
            source_dir: Source directory containing original images
            target_dir: Target directory for processed images (Hugo static directory)
        """
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)

    def process_image_path(self, image_path: str | Path) -> str:
        """
        Convert image path to Hugo format.
        All images should be referenced as /img/blog/image_name.ext

        Args:
            image_path: Original image path (relative or absolute)

        Returns:
            str: Hugo-formatted image path
        """
        # Convert to Path object for easier manipulation
        path = Path(image_path)

        # Extract just the filename
        filename = path.name

        # Return Hugo-formatted path
        return f"/img/blog/{filename}"

    def get_target_image_path(self, source_image: Path | str) -> Path:
        """
        Get the target path for an image in the Hugo static directory.

        Args:
            source_image: Path to the source image

        Returns:
            Path: Target path in Hugo static directory
        """
        source_path = Path(source_image)
        return self.target_dir / source_path.name

    def copy_image(self, source_image: Path | str) -> Path:
        """
        Copy an image to the Hugo static directory.

        Args:
            source_image: Path to the source image

        Returns:
            Path: Path to the copied image in Hugo static directory
        """
        source_path = Path(source_image)
        target_path = self.get_target_image_path(source_path)

        # Create target directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy the file, overwriting if it exists
        shutil.copy2(source_path, target_path)

        return target_path
