#!/usr/bin/env python
# public/upload_news.py
# -*- coding: utf-8 -*-
"""
推送文章到微信公众号
"""
import os
from pathlib import Path
import argparse
from typing import Optional, List, Dict
from .wx_cache import WxCache
from .wx_publisher import WxPublisher
from .wx_htmler import WxHtmler
from .md_file import MarkdownFile


def create_wx_objects(
    root_dir: Optional[str] = None,
) -> tuple[WxCache, WxPublisher, WxHtmler]:
    """创建微信相关对象"""
    if not root_dir:
        root_dir = os.getenv("CD20_ARTICLE_SOURCE")
        if not root_dir:
            raise ValueError(
                "CD20_ARTICLE_SOURCE environment variable must be set")

    cache = WxCache(root_dir=root_dir)
    publisher = WxPublisher(cache)
    htmler = WxHtmler()
    return cache, publisher, htmler


def check_missing_images(source_dir: str) -> List[Dict[str, List[str]]]:
    """检查目录下所有markdown文件中的缺失图片

    Args:
        source_dir: 源文件目录

    Returns:
        List[Dict[str, List[str]]]: 包含缺失图片信息的列表，每个元素是一个字典，
        包含 filename 和 missing_images 两个键
    """
    result = []
    pathlist = Path(source_dir).glob("**/*.md")

    for path in pathlist:
        try:
            # 提取并验证markdown文件
            md_file = MarkdownFile.extract(source_dir, path.name)

            # 获取缺失的本地图片
            broken_links = md_file.find_broken_img_links()
            if broken_links:
                # 只收集本地图片的url_in_text
                missing_images = [
                    img.url_in_text for img in broken_links if not img.external]
                if missing_images:
                    result.append({
                        "filename": path.name,
                        "missing_images": missing_images
                    })
        except Exception as e:
            print(f"Failed to process {path}: {e}")
            continue

    return result


def gen_and_upload(source_dir: str, path: Path, publisher: WxPublisher) -> bool:
    """处理单个文件

    Args:
        source_dir: 源文件目录
        path: 文件路径
        publisher: WxPublisher实例

    Returns:
        bool: 是否处理成功
    """
    try:
        path_str = str(path)
        single_file_name = path.name
        print(f"Processing file: {path_str}")

        # 提取并验证markdown文件
        md_file = MarkdownFile.extract(source_dir, single_file_name)

        # 不上传草稿
        if md_file.header.draft:
            print(f"Skipping draft: {path_str}")
            return True

        # 下载网络图片
        if not md_file.web_images_downloaded:
            try:
                md_file.download_image_from_web()
            except Exception as e:
                print(f"Failed to download images for {path_str}: {e}")
                return False
        # 如果图片不存在，则使用默认的不存在图片
        md_file.use_temp_img_for_unavailable_img()
        # 发布文章
        try:
            media_id = publisher.publish_article(md_file)
            if media_id:
                print(
                    f"Successfully published {path_str}, media_id: {media_id}")
                return True
            else:
                print(
                    f"Failed to publish {path_str}: {e}, some images are unavailable")
                return False
        except ValueError as e:
            print(f"Failed to publish {path_str}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error while publishing {path_str}: {e}")
            return False

    except Exception as e:
        print(f"Failed to process {path_str}: {e}")
        return False


def post_articles(source_dir: str) -> bool:
    """发布目录下的所有markdown文件到微信公众号

    Args:
        source_dir: 源文件目录

    Returns:
        bool: 是否全部处理成功
    """
    print(f"Source directory: {source_dir}")
    try:
        # 首先检查缺失图片
        print("Checking for missing images before publishing...")
        missing_images = check_missing_images(source_dir)
        if missing_images:
            print("\nFound missing images. Please fix them before publishing:")
            for item in missing_images:
                print(f"\nFile: {item['filename']}")
                print("Missing images:")
                for img in item["missing_images"]:
                    print(f"  - {img}")
            return False

        # 创建微信相关对象
        _, publisher, _ = create_wx_objects(source_dir)

        # 处理所有markdown文件
        success = True
        pathlist = Path(source_dir).glob("**/*.md")
        for path in pathlist:
            if not gen_and_upload(source_dir, path, publisher):
                success = False
        return success
    except Exception as e:
        print(f"Failed to process directory {source_dir}: {e}")
        return False


def main() -> int:
    """主函数

    Returns:
        int: 退出码，0表示成功，1表示失败
    """
    parser = argparse.ArgumentParser(
        description="Upload markdown files to WeChat Official Account"
    )
    parser.add_argument(
        "--source-dir",
        "-src",
        help="Directory containing markdown files (if not specified, will use WX_ARTICLE_MD_DIR environment variable)",
    )
    parser.add_argument(
        "--act",
        "-a",
        choices=["check", "post"],
        default="post",
        help="Action to perform: check for missing images or post articles",
    )
    args = parser.parse_args()

    # 如果命令行没有指定目录，则从环境变量读取
    source_dir = args.source_dir
    if not source_dir:
        source_dir = os.getenv("WX_ARTICLE_MD_DIR")
        if not source_dir:
            print("Error: No source directory specified.")
            print("Please either:")
            print("  1. Use --source-dir/-src command line argument")
            print("  2. Set WX_ARTICLE_MD_DIR environment variable")
            return 1

    if not os.path.exists(source_dir):
        print(f"Error: Directory not found: {source_dir}")
        print(
            f"Please make sure the directory exists and you have permission to access it."
        )
        return 1

    print(f"Using source directory: {source_dir}")

    if args.act == "check":
        print("Checking for missing images...")
        missing_images = check_missing_images(source_dir)
        if missing_images:
            print("\nMissing images found:")
            for item in missing_images:
                print(f"\nFile: {item['filename']}")
                print("Missing images:")
                for img in item["missing_images"]:
                    print(f"  - {img}")
            return 1
        else:
            print("No missing images found.")
            return 0
    else:
        print("Begin syncing to WeChat")
        success = post_articles(source_dir)
        return 0 if success else 1


if __name__ == "__main__":
    exit(main())
