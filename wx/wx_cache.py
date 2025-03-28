import os
import pickle
from datetime import datetime
import hashlib


class WxCache:

    def dump_cache(self):
        fp = open(self.CACHE_STORE, "wb")
        pickle.dump(self.CACHE, fp)

    def __init__(self, root_dir: str = None) -> None:
        self.CACHE = {}
        if root_dir is None:
            root_dir = os.getenv("CD20_ARTICLE_SOURCE")
        if not root_dir:
            raise ValueError(
                "root_dir must be provided or CD20_ARTICLE_SOURCE environment variable must be set"
            )

        self.ROOT_DIR = os.path.abspath(root_dir)
        if not os.path.exists(self.ROOT_DIR) or not os.path.isdir(self.ROOT_DIR):
            raise ValueError(f"Invalid directory path: {self.ROOT_DIR}")

        self.CACHE_STORE = os.path.join(self.ROOT_DIR, "Cache.bin")

        if os.path.exists(self.CACHE_STORE):
            fp = open(self.CACHE_STORE, "rb")
            self.CACHE = pickle.load(fp)
            return
        else:
            self.dump_cache()

    def __get(self, key):
        if key in self.CACHE:
            return self.CACHE[key]
        return None

    # 保存上传的图片的media_id 和 Media_url
    def set(self, file_path, media_id, media_url):
        digest = self.__file_digest(file_path)
        self.CACHE[digest] = [media_id, media_url]
        self.dump_cache()

    def get(self, file_path):
        digest = self.__file_digest(file_path)
        return self.__get(digest)

    # 更新上传的文章的media_id, 并不保存Media_url
    def update(self, file_path, media_id, media_url=None):
        digest = self.__file_digest(file_path)
        self.CACHE[digest] = [media_id, media_url]
        self.dump_cache()

    def __file_digest(self, file_path):
        """
        计算文件的md5值
        """
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            md5.update(f.read())
        return md5.hexdigest()

    def is_cached(self, file_path):
        digest = self.__file_digest(file_path)
        return self.__get(digest) != None
