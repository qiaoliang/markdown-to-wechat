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

    def publish_multi_articles(self, md_files: list[MarkdownFile]) -> list[str]:
        """发布多个文章"""
        articles = []
        to_publish = []  # 记录要发布的文章
        for md_file in md_files:
            # 检查文章是否已经在缓存中
            if self.cache.get(md_file.abs_path):
                continue
            # 不上传草稿
            if md_file.header.draft:
                print(f"Skipping draft article: {md_file.abs_path}")
                continue
            article = self.assembling_article(md_file)
            if article:
                articles.append(article)
                to_publish.append(md_file)  # 记录这篇文章需要发布
        if not articles:
            return []
        media_ids = self.client.upload_article_draft(articles)
        # 只更新需要发布的文章的缓存
        for i, media_id in enumerate(media_ids):
            self.cache.update(to_publish[i].abs_path, media_id)
        return media_ids

    def assembling_article(self, md_file: MarkdownFile) -> dict:
        if self.cache.get(md_file.abs_path):
            print(f"Skipping published article: {md_file.abs_path}")
            return None
        # 如果文章有未上传的图片，则使用临时图片
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
            # 如果文章没有图片，使用默认的缩略图
            if not md_file.uploaded_images:
                md_file.uploaded_images["assets/default_thumb.png"] = [
                    "default_media_id",
                    "default_url",
                ]
                thumb_media_id = "default_media_id"
            else:
                raise ValueError(
                    "No images found for thumbnail. At least one image is required for WeChat article."
                )
        article["thumb_media_id"] = thumb_media_id
        return article

    def publish_single_article(self, md_file: MarkdownFile) -> str:
        """发布文章的主流程"""
        article = self.assembling_article(md_file)
        if not article:
            return self.cache.get(md_file.abs_path)
        media_ids = self.client.upload_article_draft([article])
        media_id = media_ids[0]  # 获取第一个（也是唯一的）media_id
        self.cache.update(md_file.abs_path, media_id)
        return media_id
