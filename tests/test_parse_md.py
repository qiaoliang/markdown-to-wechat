import shutil
import tempfile
import pytest
import os
from wx.md_file import MarkdownHeader, MarkdownFile, MarkdownBody, ImageReference


@pytest.fixture
def temp_dir():
    # 创建临时目录
    dir_path = tempfile.mkdtemp()
    yield dir_path
    # 测试结束后，删除临时目录及其内容
    shutil.rmtree(dir_path)


def test_markdown_file_extract(temp_dir):
    """Test the static extract method of MarkdownFile class"""
    # Copy test data to temp directory
    data_dir = os.path.join(os.getcwd(), "testdata")
    if os.path.exists(data_dir):
        shutil.copytree(data_dir, temp_dir, dirs_exist_ok=True)
    else:
        print("项目根目录中 testdata 目录不存在")

    # Create necessary directories and files
    banner_dir = os.path.join(temp_dir, "banner")
    os.makedirs(banner_dir, exist_ok=True)

    # Create placeholder image files
    with open(os.path.join(banner_dir, "banner.png"), "w") as f:
        f.write("placeholder")
    with open(os.path.join(temp_dir, "exists.png"), "w") as f:
        f.write("placeholder")

    source_dir = os.path.join(temp_dir)
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
    assert isinstance(md_file.body, MarkdownBody)
    assert "This is a sample paragraph" in md_file.body.body_text
    imgList = md_file.get_imgRefs()
    assert len(imgList) == 4  # banner.png, web image, exists.png, unexists.png
    ret = md_file.find_broken_img_links()
    assert len(ret) == 1
    imgRef = ret[0]
    assert imgRef.url_in_text == "./unexists.png"
    assert imgRef.original_path == os.path.abspath(
        os.path.join(source_dir, "unexists.png")
    )
    assert imgRef.existed == False
    assert imgRef.external == False
    assert md_file.body.body_text is not ""
    assert md_file.body.source_dir is not ""
    assert md_file.body.get_imgRefs is not []


def test_markdown_header_extract(temp_dir):
    """Test the MarkdownHeader.extract method"""
    # Copy test data to temp directory
    data_dir = os.path.join(os.getcwd(), "testdata")
    if os.path.exists(data_dir):
        shutil.copytree(data_dir, temp_dir, dirs_exist_ok=True)
    else:
        print("项目根目录中 testdata 目录不存在")

    # Create necessary directories and files
    banner_dir = os.path.join(temp_dir, "banner")
    os.makedirs(banner_dir, exist_ok=True)

    # Create placeholder image files
    with open(os.path.join(banner_dir, "banner.png"), "w") as f:
        f.write("placeholder")

    # Read the markdown file content
    with open(os.path.join(temp_dir, "a_template.md"), "r", encoding="utf-8") as f:
        content = f.read()

    # Extract header content
    header_content = content.split("+++")[1].strip()
    header = MarkdownHeader.extract_header(temp_dir, header_content)

    # Verify header fields
    assert header.title == "Sample Title"
    assert header.gen_cover == True
    assert header.subtitle == "This is a sample subtitle"
    assert header.date == "2023-10-15"
    assert header.banner == "banner/banner.png"
    assert header.source_dir == temp_dir

    # Test banner image reference
    banner_ref = header.get_banner_imgRef()
    assert isinstance(banner_ref, ImageReference)
    assert banner_ref.url_in_text == "banner/banner.png"
    assert banner_ref.existed == True
    assert banner_ref.external == False


def test_markdown_body_image_refs(temp_dir):
    """Test the MarkdownBody image reference extraction"""
    # Copy test data to temp directory
    data_dir = os.path.join(os.getcwd(), "testdata")
    if os.path.exists(data_dir):
        shutil.copytree(data_dir, temp_dir, dirs_exist_ok=True)
    else:
        print("项目根目录中 testdata 目录不存在")

    # Create necessary directories and files
    assets_dir = os.path.join(temp_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    # Create placeholder image files
    with open(os.path.join(assets_dir, "exists.png"), "w") as f:
        f.write("placeholder")

    # Read the markdown file content
    with open(os.path.join(temp_dir, "a_template.md"), "r", encoding="utf-8") as f:
        content = f.read()

    # Extract body content
    body_content = content.split("+++")[2].strip()
    body = MarkdownBody(temp_dir, body_content)

    # Get image references
    img_refs = body.get_imgRefs()

    # Verify image references
    assert len(img_refs) == 3  # web image, exists.png, unexists.png

    # Verify web image
    web_img = next(ref for ref in img_refs if ref.external)
    assert web_img.url_in_text == "https://picsum.photos/id/134/400/600.jpg"
    assert web_img.external == True
    # Web images are not considered as existed until downloaded
    assert web_img.existed == False

    # Verify existing local image
    local_img = next(
        ref for ref in img_refs if ref.url_in_text == "./assets/exists.png"
    )
    assert local_img.external == False
    assert local_img.existed == True
    assert local_img.original_path == os.path.abspath(
        os.path.join(temp_dir, "assets/exists.png")
    )

    # Verify non-existing local image
    missing_img = next(ref for ref in img_refs if ref.url_in_text == "./unexists.png")
    assert missing_img.external == False
    assert missing_img.existed == False
    assert missing_img.original_path == os.path.abspath(
        os.path.join(temp_dir, "unexists.png")
    )


def test_markdown_file_download_images(temp_dir):
    """Test the download_image_from_web method"""
    # Copy test data to temp directory
    data_dir = os.path.join(os.getcwd(), "testdata")
    if os.path.exists(data_dir):
        shutil.copytree(data_dir, temp_dir, dirs_exist_ok=True)
    else:
        print("项目根目录中 testdata 目录不存在")

    # Create necessary directories and files
    banner_dir = os.path.join(temp_dir, "banner")
    os.makedirs(banner_dir, exist_ok=True)

    # Create placeholder image files
    with open(os.path.join(banner_dir, "banner.png"), "w") as f:
        f.write("placeholder")

    # Extract markdown file
    md_file = MarkdownFile.extract(temp_dir, os.path.join(temp_dir, "a_template.md"))

    # Download images
    md_file.download_image_from_web()

    # Verify web image was downloaded
    web_img = next(ref for ref in md_file.image_pairs if ref.external)
    assert web_img.existed == True
    assert os.path.exists(web_img.original_path)
    assert web_img.original_path.startswith("/tmp/")
    assert web_img.original_path.endswith(".jpg") or web_img.original_path.endswith(
        ".png"
    )
