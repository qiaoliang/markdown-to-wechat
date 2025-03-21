import os
import json
import requests
from typing import Dict, List
from .md_file import MarkdownFile
from .wx_cache import WxCache
from .wx_htmler import WxHtmler
from .image_processor import ImageProcessor
from .wx_client import WxClient


class WxPublisher:
    def __init__(self, wx_cache: WxCache):
        self.client = WxClient()
        self.cache = wx_cache
        self.htmler = WxHtmler()
        self.image_processor = ImageProcessor(self.client, wx_cache)

    def publish_article(self, md_file: MarkdownFile) -> str:
        """发布文章的主流程"""
        # 如果图片不存在，则使用默认的不存在图片
        if md_file.get_imgRefs().count(lambda x: not x.existed) > 0:
            md_file.use_temp_img_for_unavailable_img()
        # 1. 处理图片
        md_file.image_uploaded = self.image_processor.process_article_images(
            md_file)
        if not md_file.image_uploaded:
            raise ValueError("Failed to process images for article")
        # 2. 更新图片URL
        md_file.body.body_text = self.htmler.update_image_urls(
            md_file.body.body_text, md_file.uploaded_images
        )

        # 3. 生成文章内容
        article = self.htmler.generate_article(md_file)

        # 4. 添加缩略图
        thumb_media_id = self.htmler.get_thumbnail_id(md_file.uploaded_images)
        if not thumb_media_id:
            raise ValueError(
                "No images found for thumbnail. At least one image is required for WeChat article."
            )
        article["thumb_media_id"] = thumb_media_id

        # 5. 上传文章
        media_id = self.client.upload_article_draft(article)
        self.cache.update(md_file.abs_path, media_id)
        return media_id
