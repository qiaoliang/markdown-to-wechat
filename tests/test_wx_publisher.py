import os
import shutil
import tempfile
from unittest.mock import Mock, patch
import pytest
from wx.wx_publisher import WxPublisher
from wx.wx_cache import WxCache
from wx.md_file import MarkdownFile
from wx.wx_htmler import WxHtmler
from wx.image_processor import ImageProcessor


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    # Copy test data to temp directory
    testdata_dir = os.path.join(os.path.dirname(__file__), "..", "testdata")
    shutil.copytree(
        os.path.join(testdata_dir, "assets"), os.path.join(temp_dir, "assets")
    )
    shutil.copy2(
        os.path.join(testdata_dir, "a_template.md"), os.path.join(
            temp_dir, "test.md")
    )
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_wx_client():
    with patch("wx.wx_publisher.WxClient") as mock:
        client = mock.return_value
        client.upload_article_draft.side_effect = lambda articles: [
            "test_media_id"] * len(articles)
        client.upload_image.return_value = ("test_media_id", "test_url")
        yield client


@pytest.fixture
def wx_cache(temp_test_dir):
    """Create a WxCache instance with the temp directory as root"""
    cache = WxCache(root_dir=temp_test_dir)
    cache.cache_file = os.path.join(temp_test_dir, "Cache.bin")
    return cache


@pytest.fixture
def wx_publisher(wx_cache, mock_wx_client):
    publisher = WxPublisher(wx_cache)
    # Mock image processor to simulate successful image processing

    def process_images(md_file):
        md_file.image_uploaded = True
        if md_file.base_name == "test.md" or md_file.base_name == "another_article.md":
            md_file.uploaded_images = {
                "assets/exists.png": ["test_media_id", "test_url"]}
        else:
            # 对于没有图片的文章，使用默认缩略图
            md_file.uploaded_images = {
                "assets/default_thumb.png": ["default_media_id", "default_url"]
            }
        return True

    publisher.image_processor.process_article_images = Mock(
        side_effect=process_images)
    return publisher


@pytest.fixture
def test_md_file(temp_test_dir):
    """Create a MarkdownFile from the actual test data"""
    return MarkdownFile(source_dir=temp_test_dir, md_file_name="test.md")


def test_publish_article_success(wx_publisher, test_md_file):
    """Test successful article publishing with actual test data"""
    media_id = wx_publisher.publish_single_article(test_md_file)

    assert media_id == "test_media_id"
    assert wx_publisher.client.upload_article_draft.called
    assert wx_publisher.cache.get(test_md_file.abs_path) is not None


def test_publish_article_no_images(wx_publisher, temp_test_dir):
    """Test article publishing with no images (should use default thumbnail)"""
    # Create a temporary markdown file without images
    no_images_md = os.path.join(temp_test_dir, "no_images.md")
    with open(no_images_md, "w", encoding="utf-8") as f:
        f.write(
            """+++
title= "No Images Article"
author= "Test Author"
subtitle= "Test Digest"
date= "2024-03-27"
+++

# No Images Article
This article has no images.
"""
        )

    md_file = MarkdownFile(source_dir=temp_test_dir,
                           md_file_name="no_images.md")

    # Mock image processor for no images case
    def process_no_images(md_file):
        md_file.image_uploaded = True
        # 使用默认缩略图
        md_file.uploaded_images = {
            "assets/default_thumb.png": ["default_media_id", "default_url"]
        }
        return True

    wx_publisher.image_processor.process_article_images = Mock(
        side_effect=process_no_images
    )

    # 应该成功发布，使用默认缩略图
    media_id = wx_publisher.publish_single_article(md_file)
    assert media_id == "test_media_id"
    assert wx_publisher.cache.get(md_file.abs_path) is not None


def test_publish_article_image_processing_failure(wx_publisher, test_md_file):
    """Test article publishing when image processing fails"""
    # Mock image processor to simulate failure
    wx_publisher.image_processor.process_article_images = Mock(
        return_value=False)

    with pytest.raises(ValueError, match="Failed to process images for article"):
        wx_publisher.publish_single_article(test_md_file)


def test_publish_article_cache_update(wx_publisher, test_md_file):
    """Test that cache is properly updated after successful publishing"""
    media_id = wx_publisher.publish_single_article(test_md_file)

    cache_value = wx_publisher.cache.get(test_md_file.abs_path)
    assert cache_value is not None
    assert cache_value == f"{test_md_file.abs_path}:{media_id}"


def test_publish_article_with_actual_images(wx_publisher, test_md_file):
    """Test article publishing with actual test images"""
    media_id = wx_publisher.publish_single_article(test_md_file)

    assert media_id == "test_media_id"
    assert wx_publisher.client.upload_article_draft.called
    assert wx_publisher.cache.get(test_md_file.abs_path) is not None


def test_publish_multi_articles(wx_publisher, temp_test_dir):
    """Test publishing multiple articles with different scenarios"""
    # Create content for no_images.md
    with open(os.path.join(temp_test_dir, "no_images.md"), "w", encoding="utf-8") as f:
        f.write("""+++
title= "No Images Article"
author= "Test Author"
subtitle= "Test Digest"
date= "2024-03-27"
+++

# No Images Article
This article has no images.
""")

    # Create content for another_article.md with image reference
    with open(os.path.join(temp_test_dir, "another_article.md"), "w", encoding="utf-8") as f:
        f.write("""+++
title= "Another Article"
author= "Test Author"
subtitle= "Test Digest"
date= "2024-03-27"
+++

# Another Article
This article has an image:
![Test Image](assets/exists.png)
""")

    # 创建测试文件对象
    articles = [
        MarkdownFile(source_dir=temp_test_dir, md_file_name="test.md"),
        MarkdownFile(source_dir=temp_test_dir, md_file_name="no_images.md"),
        MarkdownFile(source_dir=temp_test_dir,
                     md_file_name="another_article.md")
    ]

    # 模拟图片处理
    def process_images(md_file):
        md_file.image_uploaded = True
        if md_file.base_name == "test.md" or md_file.base_name == "another_article.md":
            md_file.uploaded_images = {
                "assets/exists.png": ["test_media_id", "test_url"]}
        else:
            # 对于没有图片的文章，使用默认缩略图
            md_file.uploaded_images = {
                "assets/default_thumb.png": ["default_media_id", "default_url"]
            }
        return True

    wx_publisher.image_processor.process_article_images = Mock(
        side_effect=process_images)

    # 测试场景1：所有文章都是新的
    media_ids = wx_publisher.publish_multi_articles(articles)
    assert len(media_ids) == 3
    assert all(media_id == "test_media_id" for media_id in media_ids)

    # 验证缓存更新
    for article in articles:
        cache_value = wx_publisher.cache.get(article.abs_path)
        assert cache_value is not None
        assert cache_value == f"{article.abs_path}:test_media_id"

    # 测试场景2：尝试重新发布已经发布的文章
    new_media_ids = wx_publisher.publish_multi_articles(articles)
    assert len(new_media_ids) == 0  # 所有文章都在缓存中，应该返回空列表

    # 测试场景3：混合新文章和已发布文章
    # 创建一个新文章
    with open(os.path.join(temp_test_dir, "new_article.md"), "w", encoding="utf-8") as f:
        f.write("""+++
title= "New Article"
author= "Test Author"
subtitle= "Test Digest"
date= "2024-03-27"
+++

# New Article
This is a new article.
""")

    mixed_articles = articles + [
        MarkdownFile(source_dir=temp_test_dir, md_file_name="new_article.md")
    ]

    media_ids = wx_publisher.publish_multi_articles(mixed_articles)
    assert len(media_ids) == 1  # 只有新文章被发布
    assert media_ids[0] == "test_media_id"

    # 验证客户端调用
    assert wx_publisher.client.upload_article_draft.call_count == 2  # 应该被调用两次
