import shutil
import tempfile
import pytest
import os
from wx.md_file import MarkdownHeader, MarkdownFile, MarkdownBody, ImageReference


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def test_data_dir(temp_dir):
    """Setup test data directory with necessary files"""
    # Copy test data to temp directory
    data_dir = os.path.join(os.getcwd(), "testdata")
    if os.path.exists(data_dir):
        shutil.copytree(data_dir, temp_dir, dirs_exist_ok=True)
    else:
        print("项目根目录中 testdata 目录不存在")

    # Create necessary directories and files
    assets_dir = os.path.join(temp_dir, "assets")
    banner_dir = os.path.join(temp_dir, "banner")
    os.makedirs(assets_dir, exist_ok=True)
    os.makedirs(banner_dir, exist_ok=True)

    # Create placeholder image files
    with open(os.path.join(assets_dir, "exists.png"), "w") as f:
        f.write("placeholder")
    with open(os.path.join(banner_dir, "banner.png"), "w") as f:
        f.write("placeholder")

    return temp_dir


def test_markdown_file_extract(test_data_dir):
    """Test the static extract method of MarkdownFile class"""
    source_dir = test_data_dir
    abs_path = os.path.abspath(os.path.join(source_dir, "a_template.md"))

    # Extract markdown file
    md_file = MarkdownFile.extract(source_dir, abs_path)

    # Verify the extracted file
    assert isinstance(md_file, MarkdownFile)
    assert md_file.base_name == "a_template.md"
    assert os.path.isabs(md_file.abs_path)

    # Verify header content
    assert md_file.header.title == "Sample Title"
    assert md_file.header.gen_cover == True
    assert md_file.header.subtitle == "This is a sample subtitle"
    assert md_file.header.date == "2023-10-15"
    assert md_file.header.banner == "banner/banner.png"
    assert md_file.header.banner_imgRef.url_in_text == "banner/banner.png"
    assert md_file.header.banner_imgRef.original_path == os.path.abspath(
        os.path.join(source_dir, "banner/banner.png")
    )
    assert md_file.header.banner_imgRef.existed == True
    assert md_file.header.banner_imgRef.external == False

    # Verify body content
    assert isinstance(md_file.body, MarkdownBody)
    assert "This is a sample paragraph" in md_file.body.body_text
    assert md_file.body.source_dir == source_dir

    # Verify image references
    imgList = md_file.get_imgRefs()
    assert len(imgList) == 4  # banner.png, web image, exists.png, unexists.png


def test_markdown_header_extract(test_data_dir):
    """Test the MarkdownHeader.extract method"""
    # Read the markdown file content
    with open(os.path.join(test_data_dir, "a_template.md"), "r", encoding="utf-8") as f:
        content = f.read()

    # Extract header content
    header_content = content.split("+++")[1].strip()
    header = MarkdownHeader.extract_header(test_data_dir, header_content)

    # Verify header fields
    assert header.title == "Sample Title"
    assert header.gen_cover == True
    assert header.subtitle == "This is a sample subtitle"
    assert header.date == "2023-10-15"
    assert header.banner == "banner/banner.png"
    assert header.source_dir == test_data_dir


def test_markdown_body_image_refs(test_data_dir):
    """Test the MarkdownBody image reference extraction"""
    # Read the markdown file content
    with open(os.path.join(test_data_dir, "a_template.md"), "r", encoding="utf-8") as f:
        content = f.read()

    # Extract body content
    body_content = content.split("+++")[2].strip()
    body = MarkdownBody(test_data_dir, body_content)

    # Get image references
    img_refs = body.get_imgRefs()

    # Verify image references
    assert len(img_refs) == 3  # web image, exists.png, unexists.png

    # Verify web image
    web_img = next(ref for ref in img_refs if ref.external)
    assert web_img.url_in_text == "https://picsum.photos/id/134/400/600.jpg"
    assert web_img.external == True
    assert web_img.existed == False

    # Verify existing local image
    local_img = next(
        ref for ref in img_refs if ref.url_in_text == "./assets/exists.png"
    )
    assert local_img.external == False
    assert local_img.existed == True
    assert local_img.original_path == os.path.abspath(
        os.path.join(test_data_dir, "assets/exists.png")
    )

    # Verify non-existing local image
    missing_img = next(
        ref for ref in img_refs if ref.url_in_text == "./unexists.png")
    assert missing_img.external == False
    assert missing_img.existed == False
    assert missing_img.original_path == os.path.abspath(
        os.path.join(test_data_dir, "unexists.png")
    )


def test_markdown_file_download_images(test_data_dir):
    """Test the download_image_from_web method"""
    # Extract markdown file
    md_file = MarkdownFile.extract(
        test_data_dir, os.path.join(test_data_dir, "a_template.md"))

    # Download images
    md_file.download_image_from_web()

    # Verify web image was downloaded
    web_img = next(ref for ref in md_file.image_pairs if ref.external)
    assert web_img.existed == True
    assert os.path.exists(web_img.original_path)

    # Check if image is saved in assets directory
    assert web_img.original_path.startswith(
        os.path.join(test_data_dir, "assets"))
    assert web_img.original_path.endswith((".jpg", ".png"))

    # Verify assets directory exists
    assets_dir = os.path.join(test_data_dir, "assets")
    assert os.path.exists(assets_dir)
    assert os.path.isdir(assets_dir)

    # Verify image filename format
    filename = os.path.basename(web_img.original_path)
    assert filename.startswith("image_")
    assert filename.endswith((".jpg", ".png"))


def test_find_broken_img_links(test_data_dir):
    """Test the find_broken_img_links method to verify it correctly identifies invalid local image paths."""
    # Extract markdown file
    md_file = MarkdownFile.extract(
        test_data_dir, os.path.join(test_data_dir, "a_template.md"))

    # Get broken image links
    broken_links = md_file.find_broken_img_links()

    # Verify the results
    assert len(broken_links) == 1  # We expect one broken link in the template

    # Verify the broken link details
    broken_link = broken_links[0]
    assert broken_link.url_in_text == "./unexists.png"
    assert broken_link.external == False
    assert broken_link.existed == False
    assert broken_link.original_path == os.path.abspath(
        os.path.join(test_data_dir, "unexists.png")
    )

    # Verify that web images are not included in broken links
    web_images = [ref for ref in md_file.image_pairs if ref.external]
    assert len(web_images) > 0  # There should be web images
    # None should be in broken_links
    assert all(ref not in broken_links for ref in web_images)
