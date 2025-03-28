# Markdown to WeChat

一个用于将 Markdown 文章批量上传到微信公众号草稿箱的工具。

## 功能特点

- 支持批量上传 Markdown 文件到微信公众号
- 自动处理文章中的图片（包括本地图片和网络图片）
- 保持微信公众号文章的样式美观
- 支持文章元数据（标题、作者、摘要等）
- 自动缓存已上传的文章和图片，避免重复上传
- 支持指定文章MD文件的源目录

## 安装

1. 确保你已安装 Python 3.7+ 和 Poetry

2. 克隆项目并安装依赖：
```bash
git clone [repository-url]
cd markdown-to-wechat
poetry install
```

## 配置

### 1. 微信公众号配置

在运行之前，需要设置以下环境变量：

```bash
# 微信公众号的 APP_ID 和 APP_SECRET
export WECHAT_APP_ID="你的公众号 APP_ID"
export WECHAT_APP_SECRET="你的公众号 APP_SECRET"

# 必需：设置文章源目录（以下两种方式二选一）
export CD20_ARTICLE_SOURCE="/path/to/your/markdown/files"  # 方式1
export WX_ARTICLE_MD_DIR="/path/to/your/markdown/files"    # 方式2
```

### 2. Markdown 文件格式

文章需要包含以下 front matter：

```markdown
+++
title= "文章标题"
subtitle= "文章副标题"
date= "2024-03-20"
author= "作者名"
banner= "banner/banner.png"  # 可选：文章题图
gen_cover= "true"  # 可选：是否生成封面
draft = True
+++

# 文章内容
...
```

## 使用方法

### 基本用法

1. 使用环境变量指定的目录：
```bash
poetry run python -m wx.sync
```

2. 使用命令行参数指定目录：
```bash
poetry run python -m wx.sync --source-dir /path/to/your/markdown/files
# 或使用短参数
poetry run python -m wx.sync -src /path/to/your/markdown/files
```

### 工作流程

1. 程序会扫描指定目录下所有的 `.md` 文件
2. 对每个文件进行处理：
   - 跳过 draft = True 的草稿文章
   - 下载文章中的网络图片到本地
   - 处理文章中的图片（对不存在的图片使用默认图片）
   - 上传文章中的图片到微信素材库
   - 转换 Markdown 为微信支持的 HTML 格式
   - 上传文章到微信公众号草稿箱
   - 缓存已处理的文章信息，避免重复上传

### 注意事项

1. 文章会被上传到草稿箱，需要在微信公众号后台手动发布
2. 本地图片路径应该相对于文章所在目录
3. 网络图片会被自动下载并上传到微信素材库
4. 已处理的文章会被缓存，如需重新上传，请清除缓存

## 常见问题

1. 如果遇到权限错误，请检查微信公众号的配置是否正确
2. 如果图片上传失败，请检查图片格式是否符合微信要求
3. 如果文章格式显示异常，请检查 Markdown 语法是否正确

## 开发

1. 运行测试：
```bash
# 运行所有测试
poetry run pytest tests -v

# 运行特定测试文件
poetry run pytest tests/test_sync.py -v

# 运行特定测试用例
poetry run pytest tests/test_sync.py::test_create_wx_objects -v
```

2. 测试覆盖：
```bash
# 生成测试覆盖率报告
poetry run pytest --cov=wx tests/
```

3. 代码格式化：
```bash
poetry run black .
```

## 测试说明

项目包含以下测试模块：

- `test_sync.py`: 测试文章同步功能
  - 测试微信对象创建
  - 测试环境变量配置
  - 测试草稿文章处理
  - 测试错误处理
- `test_wx_cache.py`: 测试缓存功能
- `test_wx_publisher.py`: 测试文章发布功能
- `test_wx_htmler.py`: 测试 HTML 转换功能
- `test_image_processor.py`: 测试图片处理功能
- `test_parse_md.py`: 测试 Markdown 解析功能

## License

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！