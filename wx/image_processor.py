from typing import Dict, Tuple, Optional
from .md_file import MarkdownFile
from .wx_client import WxClient
from .wx_cache import WxCache
import os


class ImageProcessor:
    def __init__(self, wx_client: WxClient, wx_cache: WxCache):
        self.client = wx_client
        self.cache = wx_cache

    def process_article_images(self, md_file: MarkdownFile) -> bool:
        """处理文章中的所有图片"""
        if self.cache.is_cached(md_file.abs_path):
            print(f"file : {md_file.abs_path} has been uploaded.")
            return True

        img_refs = md_file.get_imgRefs()
        images = [img_ref.original_path for img_ref in img_refs]

        for image_path in images:
            media_id, media_url = self._upload_image(image_path)
            if media_id:
                md_file.uploaded_images[image_path] = [media_id, media_url]
                self.cache.set(image_path, media_id, media_url)
        return True

    def _upload_image(self, image_path: str) -> Tuple[Optional[str], Optional[str]]:
        """上传单张图片"""
        print(f"uploading image {image_path}")
        try:
            media_id, media_url = self.client.upload_permanent_media(
                image_path, os.path.basename(image_path)
            )
            print(f"file: {image_path} => media_id: {media_id}")
            return media_id, media_url
        except Exception as e:
            print(f"upload image error: {e}")
            return None, None
