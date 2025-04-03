import os
import pickle
from datetime import datetime
import hashlib
from .error_handler import (
    error_handler,
    FileSystemError,
    CacheError,
    ErrorLevel,
    RetryStrategy
)


class WxCache:

    def dump_cache(self):
        """Dump cache to file"""
        try:
            with open(self.CACHE_STORE, "wb") as fp:
                pickle.dump(self.CACHE, fp)
        except Exception as e:
            raise CacheError(
                f"Failed to dump cache to {self.CACHE_STORE}: {str(e)}")

    def __init__(self, root_dir: str = None) -> None:
        self.CACHE = {}

        # Get root directory
        if root_dir is None:
            root_dir = os.getenv("CD20_ARTICLE_SOURCE")
        if not root_dir:
            raise FileSystemError(
                "root_dir must be provided or CD20_ARTICLE_SOURCE environment variable must be set",
                ErrorLevel.ERROR
            )

        # Validate root directory
        self.ROOT_DIR = os.path.abspath(root_dir)
        if not os.path.exists(self.ROOT_DIR):
            raise FileSystemError(f"Directory does not exist: {self.ROOT_DIR}")
        if not os.path.isdir(self.ROOT_DIR):
            raise FileSystemError(f"Not a directory: {self.ROOT_DIR}")

        # Set up cache file
        self.CACHE_STORE = os.path.join(self.ROOT_DIR, "Cache.bin")

        # Load existing cache or create new one
        if os.path.exists(self.CACHE_STORE):
            try:
                with open(self.CACHE_STORE, "rb") as fp:
                    self.CACHE = pickle.load(fp)
            except Exception as e:
                raise CacheError(
                    f"Failed to load cache from {self.CACHE_STORE}: {str(e)}")
        else:
            try:
                self.dump_cache()
            except Exception as e:
                raise CacheError(
                    f"Failed to initialize cache at {self.CACHE_STORE}: {str(e)}")

    def __get(self, key: str) -> list:
        """Get value from cache"""
        return self.CACHE.get(key)

    # 保存上传的图片的media_id 和 Media_url
    @error_handler.retry(max_retries=3, strategy=RetryStrategy.LINEAR_BACKOFF)
    def set(self, file_path: str, media_id: str, media_url: str) -> None:
        """Set cache entry for file"""
        try:
            digest = self.__file_digest(file_path)
            self.CACHE[digest] = [media_id, media_url]
            self.dump_cache()
        except Exception as e:
            error_handler.handle_error(e, {
                "file": file_path,
                "media_id": media_id,
                "media_url": media_url
            })
            raise

    def get(self, file_path: str) -> list:
        """Get cache entry for file"""
        try:
            digest = self.__file_digest(file_path)
            return self.__get(digest)
        except Exception as e:
            error_handler.handle_error(e, {"file": file_path})
            return None

    # 更新上传的文章的media_id, 并不保存Media_url
    @error_handler.retry(max_retries=3, strategy=RetryStrategy.LINEAR_BACKOFF)
    def update(self, file_path: str, media_id: str, media_url: str = None) -> None:
        """Update cache entry for file"""
        try:
            digest = self.__file_digest(file_path)
            self.CACHE[digest] = [media_id, media_url]
            self.dump_cache()
        except Exception as e:
            error_handler.handle_error(e, {
                "file": file_path,
                "media_id": media_id,
                "media_url": media_url
            })
            raise

    def __file_digest(self, file_path: str) -> str:
        """Calculate file digest"""
        try:
            if not os.path.exists(file_path):
                raise FileSystemError(f"File does not exist: {file_path}")

            md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                md5.update(f.read())
            return md5.hexdigest()
        except Exception as e:
            error_handler.handle_error(e, {"file": file_path})
            raise

    def is_cached(self, file_path: str) -> bool:
        """Check if file is cached"""
        try:
            digest = self.__file_digest(file_path)
            return self.__get(digest) is not None
        except Exception as e:
            error_handler.handle_error(e, {"file": file_path})
            return False
