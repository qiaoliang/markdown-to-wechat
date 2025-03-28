import pytest
from unittest.mock import ANY
from pathlib import Path
import os
import shutil
from wx.image_processor import ImageProcessor
from wx.md_file import MarkdownFile
from wx.wx_client import WxClient
from wx.wx_cache import WxCache


@pytest.fixture
def mock_wx_client(mocker):
    return mocker.Mock(spec=WxClient)


@pytest.fixture
def image_processor(mock_wx_client, temp_test_dir):
    return ImageProcessor(mock_wx_client, WxCache(str(temp_test_dir)))


@pytest.fixture
def temp_test_dir(tmp_path):
    """创建临时测试目录并复制测试数据"""
    # 复制测试数据到临时目录
    data_dir = os.path.join(os.getcwd(), "testdata")
    if os.path.exists(data_dir):
        # 复制 a_template.md
        shutil.copy2(os.path.join(data_dir, "a_template.md"), tmp_path)

        # 创建 assets 目录并复制图片
        assets_dir = os.path.join(tmp_path, "assets")
        os.makedirs(assets_dir, exist_ok=True)
        shutil.copy2(os.path.join(data_dir, "assets", "exists.png"), assets_dir)

        # 创建 banner 目录并复制 banner.png
        banner_dir = os.path.join(assets_dir, "banner")
        os.makedirs(banner_dir, exist_ok=True)
        if os.path.exists(os.path.join(data_dir, "assets", "banner", "banner.png")):
            shutil.copy2(
                os.path.join(data_dir, "assets", "banner", "banner.png"), banner_dir
            )
    else:
        print("项目根目录中 testdata 目录不存在")
    return tmp_path


@pytest.fixture
def sample_md_file(temp_test_dir):
    """创建示例 MarkdownFile 对象"""
    # 使用临时目录中的测试文件
    md_file_name = "a_template.md"
    md_file_path = temp_test_dir / md_file_name

    # 创建 MarkdownFile 对象
    md_file = MarkdownFile(source_dir=str(temp_test_dir), md_file_name=md_file_name)
    return md_file


def test_process_article_images_when_cached(image_processor, sample_md_file):
    # Arrange
    image_processor.cache.set(
        sample_md_file.abs_path, "test_media_id", "test_media_url"
    )

    # Act
    result = image_processor.process_article_images(sample_md_file)

    # Assert
    assert result is True
    assert image_processor.cache.is_cached(sample_md_file.abs_path)
    image_processor.client.upload_permanent_media.assert_not_called()


def test_process_article_images_success(image_processor, sample_md_file):
    # Arrange
    image_processor.client.upload_permanent_media.return_value = (
        "test_media_id",
        "test_media_url",
    )
    img_refs = sample_md_file.get_imgRefs()
    assert len(img_refs) == 4
    sample_md_file.download_image_from_web()
    sample_md_file.use_temp_img_for_unavailable_img()
    # img_refs中 existed 为 False 的个数
    assert len([img_ref for img_ref in img_refs if img_ref.existed]) == 4
    # Act
    result = image_processor.process_article_images(sample_md_file)

    # Assert
    assert result is True
    assert len(sample_md_file.uploaded_images) == 3
    assert not image_processor.cache.is_cached(sample_md_file.abs_path)
    # 检查是否调用了 upload_permanent_media
    assert image_processor.client.upload_permanent_media.call_count > 0


def test_process_article_images_upload_failure(image_processor, sample_md_file):
    # Arrange
    image_processor.client.upload_permanent_media.return_value = (None, None)

    # Act
    result = image_processor.process_article_images(sample_md_file)

    # Assert
    assert result is True  # Still returns True as per implementation
    assert not image_processor.cache.is_cached(sample_md_file.abs_path)


def test_upload_image_success(image_processor, temp_test_dir):
    # Arrange
    test_image_path = str(temp_test_dir / "assets" / "exists.png")
    expected_media_id = "test_media_id"
    expected_media_url = "test_media_url"
    image_processor.client.upload_permanent_media.return_value = (
        expected_media_id,
        expected_media_url,
    )

    # Act
    media_id, media_url = image_processor._upload_image(test_image_path)

    # Assert
    assert media_id == expected_media_id
    assert media_url == expected_media_url
    image_processor.client.upload_permanent_media.assert_called_once_with(
        ANY, "exists.png"
    )


def test_upload_image_failure(image_processor, temp_test_dir):
    # Arrange
    test_image_path = str(temp_test_dir / "assets" / "exists.png")
    image_processor.client.upload_permanent_media.side_effect = Exception(
        "Upload failed"
    )

    # Act
    media_id, media_url = image_processor._upload_image(test_image_path)

    # Assert
    assert media_id is None
    assert media_url is None


def test_upload_image_when_cached(image_processor, temp_test_dir):
    """测试当图片在缓存中时，直接使用缓存中的值而不重新上传"""
    # Arrange
    test_image_path = str(temp_test_dir / "assets" / "exists.png")
    cached_media_id = "cached_media_id"
    cached_media_url = "cached_media_url"
    image_processor.cache.set(test_image_path, cached_media_id, cached_media_url)

    # Act
    media_id, media_url = image_processor._upload_image(test_image_path)

    # Assert
    assert media_id == cached_media_id
    assert media_url == cached_media_url
    # 验证没有调用 upload_permanent_media
    image_processor.client.upload_permanent_media.assert_not_called()
