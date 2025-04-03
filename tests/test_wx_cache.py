import pytest
import os
import pickle
from pathlib import Path
import shutil
from wx.wx_cache import WxCache
from wx.error_handler import FileSystemError


@pytest.fixture
def temp_dir(tmp_path):
    """创建临时测试目录"""
    # 创建测试文件
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    return tmp_path


@pytest.fixture
def cache_with_existing_data(temp_dir):
    """创建带有已存在缓存数据的 WxCache 实例"""
    cache_file = temp_dir / "Cache.bin"
    test_data = {"test_digest": ["test_media_id", "test_media_url"]}
    with open(cache_file, "wb") as f:
        pickle.dump(test_data, f)
    return WxCache(str(temp_dir))


def test_init_with_valid_dir(tmp_path):
    """测试使用有效目录初始化"""
    cache = WxCache(str(tmp_path))
    assert cache.ROOT_DIR == str(tmp_path)
    assert os.path.exists(cache.CACHE_STORE)


def test_init_with_invalid_dir():
    """测试使用无效目录初始化"""
    with pytest.raises(FileSystemError, match="Directory does not exist"):
        WxCache("/non/existent/directory")


def test_init_without_dir_and_env():
    """测试没有目录和环境变量时初始化"""
    if "CD20_ARTICLE_SOURCE" in os.environ:
        del os.environ["CD20_ARTICLE_SOURCE"]
    with pytest.raises(FileSystemError, match="root_dir must be provided"):
        WxCache()


def test_init_with_existing_cache(cache_with_existing_data):
    """测试加载已存在的缓存文件"""
    assert "test_digest" in cache_with_existing_data.CACHE
    assert cache_with_existing_data.CACHE["test_digest"] == [
        "test_media_id",
        "test_media_url",
    ]


def test_set_and_get(temp_dir):
    """测试设置和获取缓存"""
    cache = WxCache(str(temp_dir))
    test_file = temp_dir / "test.txt"

    # 设置缓存
    cache.set(str(test_file), "media_id_1", "media_url_1")

    # 获取缓存
    result = cache.get(str(test_file))
    assert result == ["media_id_1", "media_url_1"]


def test_update(temp_dir):
    """测试更新缓存"""
    cache = WxCache(str(temp_dir))
    test_file = temp_dir / "test.txt"

    # 更新缓存
    test_media_id = "test_media_id"
    cache.update(str(test_file), test_media_id)

    # 验证缓存已更新
    digest = cache._WxCache__file_digest(str(test_file))
    assert digest in cache.CACHE
    assert cache.CACHE[digest] == [test_media_id, None]


def test_is_cached(temp_dir):
    """测试检查缓存状态"""
    cache = WxCache(str(temp_dir))
    test_file = temp_dir / "test.txt"

    # 初始状态：未缓存
    assert not cache.is_cached(str(test_file))

    # 设置缓存后
    cache.set(str(test_file), "media_id_1", "media_url_1")
    assert cache.is_cached(str(test_file))


def test_cache_persistence(temp_dir):
    """测试缓存持久化"""
    # 创建缓存并设置数据
    cache1 = WxCache(str(temp_dir))
    test_file = temp_dir / "test.txt"
    cache1.set(str(test_file), "media_id_1", "media_url_1")

    # 创建新的缓存实例，验证数据是否保持
    cache2 = WxCache(str(temp_dir))
    result = cache2.get(str(test_file))
    assert result == ["media_id_1", "media_url_1"]


def test_file_digest(temp_dir):
    """测试文件摘要计算"""
    cache = WxCache(str(temp_dir))
    test_file = temp_dir / "test.txt"

    # 计算同一文件的摘要两次，应该相同
    digest1 = cache._WxCache__file_digest(str(test_file))
    digest2 = cache._WxCache__file_digest(str(test_file))
    assert digest1 == digest2

    # 修改文件内容，摘要应该不同
    test_file.write_text("different content")
    digest3 = cache._WxCache__file_digest(str(test_file))
    assert digest1 != digest3
