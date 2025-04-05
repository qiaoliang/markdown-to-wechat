from pathlib import Path
import shutil
from typing import Dict, List
from .image_reference import extract_image_references, ImageReference


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

    def extract_image_references(self, content: str) -> List[ImageReference]:
        """
        Extract all image references from markdown content.
        Reuses the functionality from image_reference module.

        Args:
            content: The markdown content to process

        Returns:
            List of ImageReference objects
        """
        return extract_image_references(content)

    def update_image_references(self, content: str, path_mapping: Dict[str, str]) -> str:
        """
        Update image references in content based on the provided path mapping.

        Args:
            content: The markdown content containing image references
            path_mapping: Dictionary mapping original image paths to new Hugo paths

        Returns:
            Updated content with new image paths
        """
        # Get all image references
        references = self.extract_image_references(content)
        updated_content = content

        # Process references in reverse order to avoid position shifts
        for ref in reversed(references):
            if ref.path in path_mapping:
                new_path = path_mapping[ref.path]
                if ref.is_html:
                    # Replace in HTML format
                    new_ref = ref.original_text.replace(
                        f'src="{ref.path}"', f'src="{new_path}"')
                    new_ref = new_ref.replace(
                        f"src='{ref.path}'", f"src='{new_path}'")
                else:
                    # Replace in Markdown format
                    new_ref = f"![{ref.alt_text}]({new_path})"
                updated_content = updated_content.replace(
                    ref.original_text, new_ref)

        return updated_content

    def copy_article_images(self, md_file: str | Path) -> Dict[str, str]:
        """
        Copy all images referenced in a markdown file to the Hugo static directory.

        Args:
            md_file: Path to the markdown file

        Returns:
            Dictionary mapping original image paths to new Hugo paths
        """
        md_file_path = Path(md_file)
        content = md_file_path.read_text()
        references = self.extract_image_references(content)
        path_mapping = {}

        for ref in references:
            # Convert relative paths to absolute
            if not Path(ref.path).is_absolute():
                source_image = md_file_path.parent / ref.path
            else:
                source_image = Path(ref.path)

            if source_image.exists():
                # Copy the image and get its new path
                target_path = self.copy_image(source_image)
                path_mapping[ref.path] = self.process_image_path(target_path)

        return path_mapping
