import os
import pytest
import tempfile
import shutil
from pathlib import Path
from wx.wx_htmler import WxHtmler
from wx.md_file import MarkdownFile

# Constants
REQUIRED_TEMPLATES = [
    "header.tmpl",
    "para.tmpl",
    "sub.tmpl",
    "link.tmpl",
    "figure.tmpl",
    "code.tmpl",
    "ref_header.tmpl",
    "ref_link.tmpl",
]

EXPECTED_STYLES = {
    "paragraph": 'style="font-size: 14px; padding-top: 8px; padding-bottom: 8px; margin: 0; line-height: 22px;"',
    "h1": 'style="margin-top: 30px; margin-bottom: 15px; padding: 0px; font-weight: bold; color: black; font-size: 24px;"',
    "h2": 'style="margin-top: 30px; margin-bottom: 15px; padding: 0px; font-weight: bold; color: black; font-size: 22px;"',
    "h3": 'style="margin-top: 30px; margin-bottom: 15px; padding: 0px; font-weight: bold; color: black; font-size: 20px;"',
}


@pytest.fixture
def temp_test_dir():
    """创建临时测试目录并复制测试数据"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 复制测试数据
        testdata_dir = Path("testdata")
        if testdata_dir.exists():
            # 复制所有文件和目录，包括 testdata/assets
            for item in testdata_dir.glob("*"):
                if item.is_file():
                    shutil.copy2(item, temp_path / item.name)
                elif item.is_dir():
                    shutil.copytree(item, temp_path / item.name)

        # 复制模板文件到 assets 目录
        assets_dir = Path("assets")
        if assets_dir.exists():
            assets_temp_dir = temp_path / "assets"
            assets_temp_dir.mkdir(exist_ok=True)
            for item in assets_dir.glob("*.tmpl"):
                shutil.copy2(item, assets_temp_dir / item.name)

        yield temp_path


@pytest.fixture
def wx_htmler(temp_test_dir):
    """创建 WxHtmler 实例"""
    htmler = WxHtmler()
    # 使用临时目录中的资源文件
    htmler.assets_dir = str(temp_test_dir / "assets")
    return htmler


@pytest.fixture
def sample_md_file(temp_test_dir):
    """创建示例 MarkdownFile 对象"""
    # 使用临时目录中的测试文件
    md_file_name = "a_template.md"

    # 创建 MarkdownFile 对象
    md_file = MarkdownFile(source_dir=str(
        temp_test_dir), md_file_name=md_file_name)
    md_file.image_uploaded = True
    md_file.uploaded_images = {
        "assets/exists.png": ["media_id_123", "https://example.com/exists.png"]
    }
    return md_file


# Helper functions


def assert_html_contains(html: str, expected_elements: list):
    """验证HTML包含所有预期的元素"""
    for element in expected_elements:
        assert element in html, f"Expected element not found: {element}"


def assert_styles_applied(html: str):
    """验证样式是否正确应用"""
    for style in EXPECTED_STYLES.values():
        assert style in html


class TestWxHtmler:
    """WxHtmler 类的测试集"""

    def test_md_to_original_html(self, wx_htmler, sample_md_file):
        """测试 Markdown 渲染功能"""
        expected_elements = [
            '<img alt="local image" src="./assets/exists.png" />',
            '<img alt="unexisted image" src="./unexists.png" />',
            '<a href="https://example.com">another page</a>',
            '<blockquote>',
            '<p>This is a blockquote.</p>',
            '</blockquote>',
        ]
        html = wx_htmler.md_to_original_html(
            sample_md_file.body.body_text, sample_md_file.uploaded_images
        )
        print(html)
        assert_html_contains(html, expected_elements)

    def test_render_markdown(self, wx_htmler, sample_md_file):
        """测试 Markdown 渲染功能"""
        html = wx_htmler.render_markdown(
            sample_md_file.body.body_text, sample_md_file.uploaded_images
        )

        expected_elements = [
            '<span class="content">Sample Title</span>',
            '<span class="content">Subheading</span>',
            '<span class="content">third Heading</span>',
            '<p style="font-size: 14px; padding-top: 8px; padding-bottom: 8px; margin: 0; line-height: 22px;">This is a sample paragraph in the markdown file. It can contain <strong>bold text</strong>, <em>italic text</em>, and other markdown features.</p>',
            "<ul>",
            "<li>List item 1</li>",
            "<li>List item 2</li>",
            '<em style="font-style: italic; color: black;">https://example.com</em>',
            '<img alt="local image" src="./assets/exists.png" />',
            '<pre class="codehilite"><code class="language-python">',
        ]
        print(html)
        print(expected_elements)
        assert_html_contains(html, expected_elements)
        assert_styles_applied(html)

    def test_css_beautify(self, wx_htmler, sample_md_file):
        """测试 CSS 美化功能"""
        html = wx_htmler.render_markdown(sample_md_file.body.body_text)
        expected_classes = ["footnotes", "codehilite"]
        assert_html_contains(
            html, [f'class="{cls}"' for cls in expected_classes])
        assert_styles_applied(html)

    def test_link_processing(self, wx_htmler, sample_md_file):
        """测试链接处理功能"""
        html = wx_htmler.render_markdown(sample_md_file.body.body_text)
        expected_classes = ["footnotes", "footnote-item", "footnote-num"]
        assert_html_contains(
            html, [f'class="{cls}"' for cls in expected_classes])

    def test_image_processing(self, wx_htmler, sample_md_file):
        """测试图片处理功能"""
        input_html = wx_htmler.md_to_original_html(
            sample_md_file.body.body_text, sample_md_file.uploaded_images
        )
        print(input_html)
        result = wx_htmler._fix_image(input_html)
        print(result)
        expected_elements = [
            "<figure",
            '<img alt="local image" src="./assets/exists.png" />',
            # '<img alt="local image" src="https://example.com/exists.png"',
            "<figcaption",
            ">local image</figcaption>",
        ]
        assert_html_contains(result, expected_elements)

    def test_code_highlighting(self, wx_htmler, sample_md_file):
        """测试代码高亮功能"""
        html = wx_htmler.render_markdown(sample_md_file.body.body_text)
        expected_elements = [
            'class="codehilite"',
            'class="language-python"',
            "# This is a code block",
            "print(&quot;Hello, World!&quot;)",
        ]
        assert_html_contains(html, expected_elements)

    def test_generate_article(self, wx_htmler, sample_md_file):
        """测试文章生成功能"""
        article = wx_htmler.generate_article(sample_md_file)

        assert article["title"] == "Sample Title"
        assert article["author"] == ""  # No author in test data
        assert article["digest"] == "This is a sample subtitle"
        assert article["show_cover_pic"] == 1
        assert (
            article["content_source_url"]
            == f"https://catcoding.me/p/{sample_md_file.base_name}"
        )
        assert isinstance(article["content"], str) and article["content"]

    def test_generate_article_without_images(self, wx_htmler, sample_md_file):
        """测试未上传图片时的错误处理"""
        sample_md_file.image_uploaded = False
        with pytest.raises(ValueError, match="Images not uploaded for article"):
            wx_htmler.generate_article(sample_md_file)

    def test_template_files_exist(self, wx_htmler):
        """测试模板文件是否存在"""
        for template in REQUIRED_TEMPLATES:
            template_path = os.path.join(wx_htmler.assets_dir, template)
            assert os.path.exists(
                template_path), f"Template file {template} not found"

    def test_temp_file_cleanup(self, wx_htmler, sample_md_file):
        """测试临时文件清理"""
        wx_htmler.render_markdown(sample_md_file.body.body_text)
        assert os.path.exists(wx_htmler.temp_html_path)

        try:
            os.remove(wx_htmler.temp_html_path)
        except OSError:
            pass

    def test_update_image_urls(self):
        htmler = WxHtmler()

        # Test case 1: Basic image replacement
        content = "![alt text](image1.jpg) and ![alt text](image2.png)"
        uploaded_images = {
            "image1.jpg": ("thumb1", "https://example.com/image1.jpg"),
            "image2.png": ("thumb2", "https://example.com/image2.png")
        }
        expected = "![alt text](https://example.com/image1.jpg) and ![alt text](https://example.com/image2.png)"
        assert htmler.update_image_urls(content, uploaded_images) == expected

        # Test case 2: Empty uploaded_images
        content = "![alt text](image1.jpg)"
        uploaded_images = {}
        assert htmler.update_image_urls(content, uploaded_images) == content

        # Test case 3: No images in content
        content = "Just some text without images"
        uploaded_images = {"image1.jpg": (
            "thumb1", "https://example.com/image1.jpg")}
        assert htmler.update_image_urls(content, uploaded_images) == content

        # Test case 4: Multiple occurrences of same image
        content = "![alt text](image1.jpg) ![alt text](image1.jpg)"
        uploaded_images = {"image1.jpg": (
            "thumb1", "https://example.com/image1.jpg")}
        expected = "![alt text](https://example.com/image1.jpg) ![alt text](https://example.com/image1.jpg)"
        assert htmler.update_image_urls(content, uploaded_images) == expected

        # Test case 5: Images with special characters
        content = "![alt text](image-1.jpg) ![alt text](image_2.png)"
        uploaded_images = {
            "image-1.jpg": ("thumb1", "https://example.com/image-1.jpg"),
            "image_2.png": ("thumb2", "https://example.com/image_2.png")
        }
        expected = "![alt text](https://example.com/image-1.jpg) ![alt text](https://example.com/image_2.png)"
        assert htmler.update_image_urls(content, uploaded_images) == expected

        # Test case 6: Multiple images in markdown content
        content = """# Sample Title
![First Image](image1.jpg)
Some text here
![Second Image](image2.png)
More text
![Third Image](image3.gif)"""
        uploaded_images = {
            "image1.jpg": ("thumb1", "https://example.com/image1.jpg"),
            "image2.png": ("thumb2", "https://example.com/image2.png"),
            "image3.gif": ("thumb3", "https://example.com/image3.gif")
        }
        expected = """# Sample Title
![First Image](https://example.com/image1.jpg)
Some text here
![Second Image](https://example.com/image2.png)
More text
![Third Image](https://example.com/image3.gif)"""
        assert htmler.update_image_urls(content, uploaded_images) == expected
