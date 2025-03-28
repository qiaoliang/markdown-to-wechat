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

        # 处理文章中的图片
        img_refs = md_file.get_imgRefs()
        images = [img_ref.original_path for img_ref in img_refs if not img_ref.external]
        print(f"Found {len(images)} local images in content")

        for image_path in images:
            if not os.path.exists(image_path):
                print(f"Image {image_path} does not exist, skipping...")
                continue
            # 图片不在缓存中，需要上传
            media_id, media_url = self._upload_image(image_path)
            if media_id:
                md_file.uploaded_images[image_path] = [media_id, media_url]
                self.cache.set(image_path, media_id, media_url)

        # 处理banner图片
        if md_file.header and md_file.header.banner:
            # banner图片应该放在 assets/banner 目录下
            banner_path = os.path.join(
                md_file.source_dir,
                "assets",
                "banner",
                os.path.basename(md_file.header.banner),
            )
            if os.path.exists(banner_path):
                media_id, media_url = self._upload_image(banner_path)
                if media_id:
                    md_file.uploaded_images[banner_path] = [media_id, media_url]
                    self.cache.set(banner_path, media_id, media_url)
            else:
                print(f"Banner image {banner_path} does not exist, skipping...")

        return True

    def _upload_image(self, image_path: str) -> Tuple[Optional[str], Optional[str]]:
        # 先检查图片是否已经在缓存中
        cache_value = self.cache.get(image_path)
        if cache_value:
            media_id, media_url = cache_value
            print(f"Image {image_path} found in cache with media_id: {media_id}")
            return media_id, media_url
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
