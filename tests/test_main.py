#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test cases for main.py
"""
import pytest
from pathlib import Path
from wx.main import check_missing_images
from wx.md_file import MarkdownFile


def test_check_missing_images_no_missing(tmp_path):
    """测试当所有图片都存在时的情况"""
    # 准备测试数据
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    test_file = test_dir / "test1.md"
    test_file.write_text("""+++
title = "Test Article"
date = "2024-03-29"
tags = ["test"]
+++
# Test Article
![test1](https://example.com/image1.jpg)
![test2](images/image2.png)
![test3](https://example.com/image3.jpg)
""")

    # 创建本地图片
    images_dir = test_dir / "images"
    images_dir.mkdir()
    (images_dir / "image2.png").touch()

    # 执行测试
    result = check_missing_images(test_dir)

    # 验证结果
    assert result == []


def test_check_missing_images_with_missing(tmp_path):
    """测试当有图片缺失时的情况"""
    # 准备测试数据
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    test_file = test_dir / "test2.md"
    test_file.write_text("""+++
title = "Test Article"
date = "2024-03-29"
tags = ["test"]
+++
# Test Article
![test1](https://example.com/image1.jpg)
![test2](images/missing.png)
![test3](https://example.com/image3.jpg)
""")

    # 创建images目录但不创建图片
    images_dir = test_dir / "images"
    images_dir.mkdir()

    # 执行测试
    result = check_missing_images(test_dir)

    # 验证结果
    assert len(result) == 1
    assert result[0]["filename"] == "test2.md"
    assert result[0]["missing_images"] == ["images/missing.png"]


def test_check_missing_images_empty_directory(tmp_path):
    """测试空目录的情况"""
    test_dir = tmp_path / "empty_dir"
    test_dir.mkdir()

    result = check_missing_images(test_dir)
    assert result == []


def test_check_missing_images_invalid_file(tmp_path):
    """测试无效markdown文件的情况"""
    # 准备测试数据
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    test_file = test_dir / "invalid.md"
    test_file.write_text("""+++
title = "Invalid Article"
date = "2024-03-29"
tags = ["test"]
+++
# Invalid Article
This is not a valid markdown file with image references
""")

    # 执行测试
    result = check_missing_images(test_dir)
    assert result == []


def test_check_missing_images_multiple_files(tmp_path):
    """测试多个文件的情况"""
    # 准备测试数据
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()

    # 创建第一个文件，所有图片都存在
    test_file1 = test_dir / "test1.md"
    test_file1.write_text("""+++
title = "Test Article 1"
date = "2024-03-29"
tags = ["test"]
+++
# Test Article 1
![test1](images/image1.png)
![test2](https://example.com/image2.jpg)
""")

    # 创建第二个文件，有缺失的图片
    test_file2 = test_dir / "test2.md"
    test_file2.write_text("""+++
title = "Test Article 2"
date = "2024-03-29"
tags = ["test"]
+++
# Test Article 2
![test3](images/image3.png)
![test4](images/missing.png)
![test5](https://example.com/image5.jpg)
""")

    # 创建images目录和存在的图片
    images_dir = test_dir / "images"
    images_dir.mkdir()
    (images_dir / "image1.png").touch()
    (images_dir / "image3.png").touch()

    # 执行测试
    result = check_missing_images(test_dir)

    # 验证结果
    assert len(result) == 1
    assert result[0]["filename"] == "test2.md"
    assert result[0]["missing_images"] == ["images/missing.png"]
