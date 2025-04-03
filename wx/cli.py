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
from .error_handler import (
    error_handler,
    FileSystemError,
    ValidationError,
    ImageError,
    APIError,
    ErrorLevel,
    RetryStrategy
)


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
    path_str = str(path)
    try:
        single_file_name = path.name
        error_handler.logger.info(f"Processing file: {path_str}")

        # 提取并验证markdown文件
        try:
            md_file = MarkdownFile.extract(source_dir, single_file_name)
        except Exception as e:
            raise ValidationError(f"Failed to extract markdown file: {str(e)}")

        # 不上传草稿
        if md_file.header.draft:
            error_handler.logger.info(f"Skipping draft: {path_str}")
            return True

        # 下载网络图片
        if not md_file.web_images_downloaded:
            try:
                md_file.download_image_from_web()
            except Exception as e:
                raise ImageError(f"Failed to download images: {str(e)}")

        # 如果图片不存在，则使用默认的不存在图片
        md_file.use_temp_img_for_unavailable_img()

        # 发布文章
        try:
            media_id = publisher.publish_single_article(md_file)
            if media_id:
                error_handler.logger.info(
                    f"Successfully published {path_str}, media_id: {media_id}")
                return True
            else:
                raise APIError("Failed to get media_id from WeChat API")
        except ValueError as e:
            raise ValidationError(f"Invalid article format: {str(e)}")
        except Exception as e:
            raise APIError(f"Failed to publish article: {str(e)}")

    except Exception as e:
        error_handler.handle_error(
            e, {"file": path_str, "source_dir": source_dir})
        return False


@error_handler.retry(max_retries=3, strategy=RetryStrategy.LINEAR_BACKOFF)
def post_articles(source_dir: str) -> bool:
    """发布目录下的所有markdown文件到微信公众号

    Args:
        source_dir: 源文件目录

    Returns:
        bool: 是否全部处理成功
    """
    error_handler.logger.info(f"Source directory: {source_dir}")

    if not os.path.exists(source_dir):
        raise FileSystemError(f"Source directory does not exist: {source_dir}")

    try:
        # 创建微信相关对象
        _, publisher, _ = create_wx_objects(source_dir)

        # 收集所有 markdown 文件
        md_files = []
        pathlist = Path(source_dir).glob("**/*.md")

        for path in pathlist:
            try:
                # 提取并验证markdown文件
                md_file = MarkdownFile.extract(source_dir, path.name)
                # 检查缺失图片
                broken_links = md_file.find_broken_img_links()
                if broken_links:
                    error_details = {
                        "file": path.name,
                        "missing_images": [img.url_in_text for img in broken_links]
                    }
                    raise ImageError(
                        f"Found {len(broken_links)} missing images in {path.name}",
                        ErrorLevel.ERROR
                    )
                md_files.append(md_file)
            except Exception as e:
                error_handler.handle_error(e, {"file": str(path)})
                continue

        if not md_files:
            raise ValidationError(
                "No valid markdown files found to publish",
                ErrorLevel.WARNING
            )

        # 使用 publisher 的发布功能
        media_ids = publisher.publish_multi_articles(md_files)
        if not media_ids:
            raise APIError("Failed to publish any articles", ErrorLevel.ERROR)

        error_handler.logger.info(
            f"Successfully published {len(media_ids)} articles")
        return True

    except Exception as e:
        error_handler.handle_error(e, {"source_dir": source_dir})
        return False


def main() -> int:
    """主函数

    用法示例:
        poetry run sync --source-dir /path/to/markdown/files  # 发布文章
        poetry run sync -src /path/to/markdown/files         # 使用短参数
        poetry run sync --source-dir ./articles --act check  # 只检查图片

    环境变量:
        WX_ARTICLE_MD_DIR: 可选，指定 markdown 文件目录
        如果设置了此环境变量，可以不使用 --source-dir 参数

    Returns:
        int: 退出码，0表示成功，1表示失败
    """
    parser = argparse.ArgumentParser(
        description="上传 markdown 文件到微信公众号",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,  # 禁用参数前缀匹配
        epilog="""
示例:
    %(prog)s --source-dir ./articles          # 发布 articles 目录下的文章
    %(prog)s -src ./articles                  # 同上，使用短参数
    %(prog)s --source-dir ./articles --act check  # 只检查图片是否缺失
    %(prog)s --act check                      # 使用环境变量中的目录检查图片

环境变量:
    WX_ARTICLE_MD_DIR: 可选，指定 markdown 文件目录
    如果设置了此环境变量，可以不使用 --source-dir 参数
        """
    )
    parser.add_argument(
        "--source-dir",
        "-src",
        "--dir",  # 添加 --dir 作为显式别名
        help="markdown 文件所在目录（如果不指定，将使用 WX_ARTICLE_MD_DIR 环境变量）",
    )
    parser.add_argument(
        "--act",
        "-a",
        choices=["check", "post"],
        default="post",
        help="执行的操作：check - 只检查缺失的图片；post - 发布文章（默认）",
    )
    args = parser.parse_args()

    # 处理源目录参数
    source_dir = args.source_dir
    if not source_dir:
        source_dir = os.getenv("WX_ARTICLE_MD_DIR")
        if not source_dir:
            print("\n错误：未指定源目录")
            print("请通过以下方式之一指定目录：")
            print("  1. 使用命令行参数：--source-dir 或 -src")
            print("  2. 设置环境变量：WX_ARTICLE_MD_DIR")
            print("\n示例：")
            print("  poetry run sync --source-dir ./articles")
            print("  或")
            print("  export WX_ARTICLE_MD_DIR=./articles")
            print("  poetry run sync")
            return 1
        else:
            print(f"\n使用环境变量中的目录：{source_dir}")
            response = input("是否继续？(y/N): ").lower()
            if response != 'y':
                print("操作已取消")
                return 0

    # 验证目录是否存在
    if not os.path.exists(source_dir):
        print(f"\n错误：目录不存在：{source_dir}")
        print("请确保目录存在且有访问权限")
        return 1

    # 验证目录是否可访问
    if not os.access(source_dir, os.R_OK):
        print(f"\n错误：无法访问目录：{source_dir}")
        print("请确保有目录的读取权限")
        return 1

    # 验证目录中是否有 markdown 文件
    md_files = list(Path(source_dir).glob("**/*.md"))
    if not md_files:
        print(f"\n警告：目录 {source_dir} 中没有找到 markdown 文件")
        response = input("是否继续？(y/N): ").lower()
        if response != 'y':
            print("操作已取消")
            return 0

    print(f"\n使用目录：{source_dir}")
    print(f"找到 {len(md_files)} 个 markdown 文件")

    if args.act == "check":
        print("\n开始检查缺失图片...")
        missing_images = check_missing_images(source_dir)
        if missing_images:
            print("\n发现缺失的图片：")
            for item in missing_images:
                print(f"\n文件：{item['filename']}")
                print("缺失的图片：")
                for img in item["missing_images"]:
                    print(f"  - {img}")
            return 1
        else:
            print("\n未发现缺失的图片")
            return 0
    else:
        print("\n开始同步到微信公众号...")
        success = post_articles(source_dir)
        return 0 if success else 1


if __name__ == "__main__":
    exit(main())
