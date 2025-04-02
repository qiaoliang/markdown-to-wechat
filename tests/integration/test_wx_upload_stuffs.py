import pytest
from wx.md_file import MarkdownFile
from PIL import Image, ImageDraw
import os
import shutil
from wx.wx_client import WxClient
from wx.wx_cache import WxCache
from wx.image_processor import ImageProcessor
from wx.wx_publisher import WxPublisher
from wx.wx_htmler import WxHtmler


@pytest.mark.skip(reason="skip")
def create_test_image(path, size=(900, 300), colors=None):
    """创建测试图片，使用渐变效果"""
    if colors is None:
        colors = [(255, 0, 0), (0, 255, 0)]  # 默认红绿渐变

    # 创建新图片
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)

    # 创建渐变效果
    for y in range(size[1]):
        # 计算当前行的颜色
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * y / size[1])
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * y / size[1])
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * y / size[1])
        # 绘制一行
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))

    # 保存图片，使用正确的格式名称
    format_map = {".jpg": "JPEG", ".png": "PNG"}
    img_format = format_map.get(path.suffix.lower(), "PNG")
    img.save(path, format=img_format)
    return path


@pytest.mark.skip(reason="skip")
def test_process_article_images_with_multiple_images(tmp_path):
    """测试处理文章中的多张图片"""
    # 创建测试目录
    test_dir = tmp_path / "test_process_article_images_wi0"
    test_dir.mkdir()
    banner_dir = test_dir / "banner"
    banner_dir.mkdir()

    # 创建测试文件
    md_content = """+++
title= "Test Article"
gen_cover= "true"
author = "Test Author"
draft= "false"
subtitle= "This is a test subtitle"
date= "2024-03-20"
banner= "banner/banner.png"
+++

# Test Article

![banner](banner/banner.png)

This is a test article with multiple images.

![image1](image1.jpg)
![image2](image2.jpg)
"""
    md_file = test_dir / "test.md"
    md_file.write_text(md_content)

    # 创建测试图片
    banner_path = create_test_image(
        banner_dir / "banner.png", colors=[(255, 0, 0), (0, 0, 255)]  # 红蓝渐变
    )
    image1_path = create_test_image(
        test_dir / "image1.jpg", colors=[(0, 255, 0), (255, 0, 0)]  # 绿红渐变
    )
    image2_path = create_test_image(
        test_dir / "image2.jpg", colors=[(0, 0, 255), (0, 255, 0)]  # 蓝绿渐变
    )

    # 验证文件创建成功
    assert banner_path.exists()
    assert image1_path.exists()
    assert image2_path.exists()

    # 验证文件大小
    print("\n=== Test Files ===")
    print(f"Markdown file size: {md_file.stat().st_size} bytes")
    print(f"Banner file size: {banner_path.stat().st_size} bytes")
    print(f"Image1 file size: {image1_path.stat().st_size} bytes")
    print(f"Image2 file size: {image2_path.stat().st_size} bytes")

    # 创建 MarkdownFile 实例
    md = MarkdownFile(source_dir=str(test_dir), md_file_name="test.md")

    # 创建 WxClient 和 WxCache 实例
    wx_client = WxClient()
    wx_cache = WxCache(root_dir=str(test_dir))

    # 创建 ImageProcessor 实例
    image_processor = ImageProcessor(wx_client, wx_cache)

    # 处理图片
    print("\n=== Processing Images ===")
    result = image_processor.process_article_images(md)
    assert result is True

    # 验证缓存
    print("\n=== Cache Results ===")
    image1_cache = wx_cache.get(str(image1_path))
    image2_cache = wx_cache.get(str(image2_path))
    banner_cache = wx_cache.get(str(banner_path))

    print(f"Image1 cache: {image1_cache}")
    print(f"Image2 cache: {image2_cache}")
    print(f"Banner cache: {banner_cache}")

    # 验证缓存数据
    assert image1_cache is not None
    assert image2_cache is not None
    assert banner_cache is not None
    assert image1_cache[0] != image2_cache[0]  # 确保两个图片的 media_id 不同
    assert image1_cache[1] != image2_cache[1]  # 确保两个图片的 URL 不同


def test_publish_article_with_multiple_images(tmp_path):
    """测试发布包含多张图片的文章"""
    # 创建测试目录
    test_dir = tmp_path / "test_publish_article_with_multiple_images"
    test_dir.mkdir()
    banner_dir = test_dir / "banner"
    banner_dir.mkdir()
    assets_dir = test_dir / "assets"
    assets_dir.mkdir()

    # 创建测试文件
    md_content = """+++
title= "Test Article"
gen_cover= "true"
author = "Test Author"
draft= "false"
subtitle= "This is a test subtitle"
date= "2024-03-20"
banner= "banner/banner.png"
+++

# Test Article

This is a test article with multiple images.

![image1](image1.jpg)
![image2](assets/image2.jpg)

## Section 1

This is section 1 with some text.

## Section 2

This is section 2 with some text.

```python
print("this is a loooooong code block.this is a loooooong code block.this is a loooooong code block.this is a loooooong code block.")
print("Hello, World!  - 1")
print("Hello, World!  - 2")
print("Hello, World!  - 3")
print("Hello, World!  - 4")
print("Hello, World!  - 5")
print("Hello, World!  - 6")
print("Hello, World!  - 7")
print("Hello, World!  - 8")
print("Hello, World!  - 9")
print("Hello, World!  - 10")
```

"""
    md_file = test_dir / "test.md"
    md_file.write_text(md_content)

    # 创建测试图片
    banner_path = create_test_image(
        banner_dir / "banner.png", colors=[(255, 0, 0), (0, 0, 255)]  # 红蓝渐变
    )
    image1_path = create_test_image(
        test_dir / "image1.jpg", colors=[(0, 255, 0), (255, 0, 0)]  # 绿红渐变
    )
    image2_path = create_test_image(
        assets_dir / "image2.jpg", colors=[(0, 0, 255), (0, 255, 0)]  # 蓝绿渐变
    )

    # 验证文件创建成功
    assert banner_path.exists()
    assert image1_path.exists()
    assert image2_path.exists()

    # 验证文件大小
    print("\n=== Test Files ===")
    print(f"Markdown file size: {md_file.stat().st_size} bytes")
    print(f"Banner file size: {banner_path.stat().st_size} bytes")
    print(f"Image1 file size: {image1_path.stat().st_size} bytes")
    print(f"Image2 file size: {image2_path.stat().st_size} bytes")

    # 创建所需的实例
    wx_client = WxClient()
    wx_cache = WxCache(root_dir=str(test_dir))
    wx_htmler = WxHtmler()
    image_processor = ImageProcessor(wx_client, wx_cache)
    wx_publisher = WxPublisher(wx_cache)

    # 创建 MarkdownFile 实例
    md = MarkdownFile(source_dir=str(test_dir), md_file_name="test.md")

    # 发布文章
    print("\n=== Publishing Article ===")
    media_id = wx_publisher.publish_single_article(md)

    # 验证发布结果
    print("\n=== Publishing Results ===")
    print(f"Media ID: {media_id}")
    assert media_id is not None
    assert isinstance(media_id, str)
    assert len(media_id) > 0

    # 验证缓存
    print("\n=== Cache Results ===")
    article_cache = wx_cache.get(str(md_file))
    image1_cache = wx_cache.get(str(image1_path))
    image2_cache = wx_cache.get(str(image2_path))
    banner_cache = wx_cache.get(str(banner_path))

    print(f"Article cache: {article_cache}")
    print(f"Image1 cache: {image1_cache}")
    print(f"Image2 cache: {image2_cache}")
    print(f"Banner cache: {banner_cache}")

    # 验证缓存数据
    assert article_cache is not None
    assert image1_cache is not None
    assert image2_cache is not None
    assert banner_cache is not None
    assert image1_cache[0] != image2_cache[0]  # 确保两个图片的 media_id 不同
    assert image1_cache[1] != image2_cache[1]  # 确保两个图片的 URL 不同
    assert article_cache == [media_id, None]  # 验证文章缓存格式
