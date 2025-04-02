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
    "sub_num.tmpl",
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
        print(f"Checking element: {element}")
        assert element in html, f"Expected element not found: {element}"


def assert_styles_applied(html: str):
    """验证样式是否正确应用"""
    expected_style_patterns = [
        'margin-top: 30px',
        'margin-bottom: 15px',
        'padding: 0px',
        'font-weight: bold',
        'color: black',
    ]
    for pattern in expected_style_patterns:
        assert pattern in html, f"Missing style pattern: {pattern}"


class TestWxHtmler:
    """WxHtmler 类的测试集"""

    def test_md_to_original_html(self, wx_htmler, sample_md_file):
        """测试 Markdown 渲染功能"""
        expected_elements = [
            '<img alt="local image" src="./assets/exists.png" />',
            '<img alt="unexisted image" src="./unexists.png" />',
            '<a href="https://example.com">another page</a>',
            "<blockquote>",
            "<p>This is a blockquote.</p>",
            "</blockquote>",
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
            '>Sample Title<',
            '>Subheading<',
            '>third Heading<',
            '<p style="font-size: 14px; padding-top: 8px; padding-bottom: 8px; margin: 0; line-height: 22px;">This is a sample paragraph in the markdown file. It can contain <strong>bold text</strong>, <em>italic text</em>, and other markdown features.</p>',
            "<ul>",
            "<li>List item 1</li>",
            "<li>List item 2</li>",
            '<em style="font-style: italic; color: black;">https://example.com</em>',
            '<img alt="local image" src="./assets/exists.png" />',
            '<pre class="codehilite"',
            '<code class="language-python">',
        ]
        assert_html_contains(html, expected_elements)
        assert_styles_applied(html)

    def test_css_beautify(self, wx_htmler, sample_md_file):
        """测试 CSS 美化功能"""
        html = wx_htmler.render_markdown(sample_md_file.body.body_text)
        expected_classes = ["footnotes", "codehilite"]
        assert_html_contains(
            html, [f'class="{cls}"' for cls in expected_classes])

        expected_style_patterns = [
            'margin-top: 30px',
            'margin-bottom: 15px',
            'padding: 0px',
            'font-weight: bold',
            'color: black',
        ]
        for pattern in expected_style_patterns:
            assert pattern in html, f"Missing style pattern: {pattern}"

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

    def test_code_block_css_generation(self, wx_htmler):
        """测试代码块的 HTML 生成
        验证：
        1. 代码块的样式（class="codehilite"）
        2. 代码块的缩进和格式保持
        3. 代码块中的特殊字符处理
        """
        markdown_content = """
# Code Style Test

Here's a code block with style:
```python
def process_data(data):
    # Process input data
    result = {
        "name": "Test & Demo",
        "value": "<special>",
        "items": [
            "item1",
            "item2"
        ]
    }
    return result
```

End of test.
"""
        html = wx_htmler.render_markdown(markdown_content)

        # 打印生成的 HTML，方便调试
        print("\n=== Generated HTML ===")
        print(html)
        print("=== End of HTML ===\n")

        # 验证代码块样式
        expected_style = [
            '<pre class="codehilite" style="background: #272822; border-radius: 3px; word-wrap: break-word; overflow: scroll; padding: 12px 13px; line-height: 125%; color: white; font-size: 11px;">',
            '<code class="language-python">',
            '</code></pre>'
        ]
        for element in expected_style:
            assert element in html, f"Missing code block style element: {element}"

        # 验证代码缩进和格式
        expected_code = [
            'def process_data(data):',
            '    # Process input data',
            '    result = {',
            '        &quot;name&quot;: &quot;Test &amp; Demo&quot;,',
            '        &quot;value&quot;: &quot;&lt;special&gt;&quot;,',
            '        &quot;items&quot;: [',
            '            &quot;item1&quot;,',
            '            &quot;item2&quot;',
            '        ]',
            '    }',
            '    return result'
        ]
        for line in expected_code:
            print(f"Checking line: {line}")  # 打印正在检查的行
            assert line in html, f"Missing or incorrect code line: {line}"

        # 验证特殊字符处理
        expected_special = [
            '&lt;special&gt;',  # HTML 特殊字符
            'Test &amp; Demo',  # & 符号
            '&quot;item1&quot;',  # 引号
            '&quot;item2&quot;'   # 引号
        ]
        for special in expected_special:
            print(f"Checking special: {special}")  # 打印正在检查的特殊字符
            assert special in html, f"Special character not properly escaped: {special}"

    def test_generate_article(self, wx_htmler, sample_md_file):
        """测试文章生成功能"""
        article = wx_htmler.generate_article(sample_md_file)

        assert article["title"] == "Sample Title"
        assert article["author"] == ""  # No author in test data
        assert article["digest"] == "This is a sample subtitle"
        assert article["show_cover_pic"] == 1
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

    def test_update_image_urls(self):
        htmler = WxHtmler()

        # Test case 1: Basic image replacement
        content = "![alt text](image1.jpg) and ![alt text](image2.png)"
        uploaded_images = {
            "image1.jpg": ("thumb1", "https://example.com/image1.jpg"),
            "image2.png": ("thumb2", "https://example.com/image2.png"),
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
            "image_2.png": ("thumb2", "https://example.com/image_2.png"),
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
            "image3.gif": ("thumb3", "https://example.com/image3.gif"),
        }
        expected = """# Sample Title
![First Image](https://example.com/image1.jpg)
Some text here
![Second Image](https://example.com/image2.png)
More text
![Third Image](https://example.com/image3.gif)"""
        assert htmler.update_image_urls(content, uploaded_images) == expected

    def test_h2_numbering(self, wx_htmler):
        """测试 h2 标题的编号和样式
        验证：
        1. h2 标题有红色圆形背景的数字
        2. 数字按顺序递增
        3. 其他标题（h1, h3）保持原样
        """
        markdown_content = """
# First Title
## Second Title 1
### Third Title 1
## Second Title 2
### Third Title 2
## Second Title 3
# Another First Title
## Second Title 4
### Third Title 3
"""
        html = wx_htmler.render_markdown(markdown_content)

        # 验证 h2 标题的样式
        expected_h2_patterns = [
            # 检查红色圆形背景
            'background-color: #B25D55',
            'border-radius: 50%',
            # 检查数字
            '>1</section>',
            '>2</section>',
            '>3</section>',
            '>4</section>',
            # 检查标题文本
            '>Second Title 1<',
            '>Second Title 2<',
            '>Second Title 3<',
            '>Second Title 4<',
        ]

        # 验证其他标题的样式
        expected_other_patterns = [
            # h1 标题
            '>First Title<',
            '>Another First Title<',
            # h3 标题
            '>Third Title 1<',
            '>Third Title 2<',
            '>Third Title 3<',
        ]

        # 验证所有预期模式都存在于生成的 HTML 中
        for pattern in expected_h2_patterns:
            assert pattern in html, f"Missing h2 pattern: {pattern}"

        for pattern in expected_other_patterns:
            assert pattern in html, f"Missing header pattern: {pattern}"

        # 验证 h2 标题的顺序
        h2_positions = [html.find(title) for title in [
            "Second Title 1", "Second Title 2", "Second Title 3", "Second Title 4"]]
        assert h2_positions == sorted(
            h2_positions), "H2 titles are not in correct order"

        # 验证数字的顺序
        number_positions = [html.find(f'>{i}</section>') for i in range(1, 5)]
        assert number_positions == sorted(
            number_positions), "H2 numbers are not in correct order"
