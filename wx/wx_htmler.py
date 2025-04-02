import markdown
from markdown.extensions import codehilite
from pyquery import PyQuery
import html
import os
from typing import Optional, Dict
from .md_file import MarkdownFile
import re
import tempfile
from datetime import datetime


class WxHtmler:

    def __init__(self):
        self.assets_dir = "./assets"
        self.uploaded_images = {}
        self.debug = True  # 默认关闭调试模式
        self.debug_dir = os.path.join(self.assets_dir, "wx_html_debug")
        # 确保调试目录存在
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)

    def generate_article(self, md_file: MarkdownFile) -> dict:
        """生成文章对象"""
        if not md_file.image_uploaded:
            raise ValueError(
                "Images not uploaded for article. Please upload images first."
            )

        # 渲染 markdown 生成 html 的内容
        content = self.render_markdown(md_file.body.body_text)

        # 获取文章属性，与 content 一起组装成文章对象
        header = md_file.header
        article = {
            "title": header.title,
            "author": header.author,
            "digest": header.subtitle,
            "show_cover_pic": 1,  # 是否显示封面图片，1 表示显示，0 表示不显示
            "content": content,
            # "content_source_url": f"https://catcoding.me/p/{md_file.base_name}",
        }
        return article

    def render_markdown(self, content: str, uploaded_images: dict = None) -> str:
        """渲染 Markdown 内容为 HTML"""
        html_content = self.md_to_original_html(content, uploaded_images)
        return self.__css_beautify(html_content)

    def md_to_original_html(self, content: str, uploaded_images: dict = None) -> str:
        """渲染 Markdown 内容为 HTML"""
        if uploaded_images:
            self.uploaded_images = uploaded_images
        exts = [
            "markdown.extensions.extra",
            "markdown.extensions.tables",
            "markdown.extensions.toc",
            "markdown.extensions.sane_lists",
            codehilite.makeExtension(
                guess_lang=False, noclasses=True, pygments_style="monokai"
            ),
        ]
        html_content = markdown.markdown(content, extensions=exts)
        # 保存调试文件
        self._save_debug_html(content, "before_css")
        return html_content

    def __css_beautify(self, content: str) -> str:
        """美化 HTML 内容"""
        content = self._replace_para(content)
        content = self._replace_header(content)
        content = self._replace_links(content)
        content = self._format_fix(content)
        content = self._fix_image(content)
        content = self._gen_css("header") + content + "</section>"

        # 保存调试文件
        self._save_debug_html(content, "after_css")

        return content

    def _replace_para(self, content: str) -> str:
        """替换段落标签样式"""
        res = []
        for line in content.split("\n"):
            if line.startswith("<p>"):
                line = line.replace("<p>", self._gen_css("para"))
            res.append(line)
        return "\n".join(res)

    def _gen_css(self, path: str, *args) -> str:
        """生成 CSS 样式"""
        template_path = os.path.join(self.assets_dir, f"{path}.tmpl")
        with open(template_path, "r", encoding="utf-8") as f:
            tmpl = f.read()
        return tmpl.format(*args)

    def _replace_header(self, content: str) -> str:
        """替换标题标签样式
        这个方法处理 HTML 中的标题标签（h1-h6），为其添加自定义样式。
        对于 h2 标签，使用特殊的带编号样式（sub_num.tmpl）
        对于其他标签，使用普通样式（sub.tmpl）
        """
        res = []
        h2_counter = 1  # 跟踪 h2 的序号

        # 首先计算文档中 h2 的总数
        pq = PyQuery(content)
        h2_tags = pq('h2')
        total_h2 = len(h2_tags)

        for line in content.split("\n"):
            l = line.strip()
            if l.startswith("<h") and l.endswith(">"):
                tag = l.split(" ")[0].replace("<", "")
                value = l.split(">")[1].split("<")[0]
                digit = tag[1]
                font = (
                    (18 + (4 - int(tag[1])) * 2)
                    if (digit >= "0" and digit <= "9")
                    else 18
                )

                if tag == "h2":
                    # 对于 h2 标签，使用带编号的特殊模板
                    res.append(self._gen_css("sub_num", tag,
                               str(h2_counter), font, value, tag))
                    h2_counter += 1
                else:
                    # 其他标签使用普通模板
                    res.append(self._gen_css("sub", tag, font, value, tag))
            else:
                res.append(line)
        return "\n".join(res)

    def _replace_links(self, content: str) -> str:
        """替换链接样式"""
        pq = PyQuery(content)

        links = pq("a")
        refs = []
        index = 1

        if len(links) == 0:
            return content

        for l in links.items():
            link = self._gen_css("link", l.text(), index)
            index += 1
            refs.append([l.attr("href"), l.text(), link])

        for r in refs:
            orig = f'<a href="{html.escape(r[0])}">{r[1]}</a>'
            content = content.replace(orig, r[2])

        content = content + "\n" + self._gen_css("ref_header")
        content = content + """<section class="footnotes">"""

        for index, r in enumerate(refs, 1):
            line = self._gen_css("ref_link", index, r[1], r[0])
            content += line + "\n"

        content = content + "</section>"
        return content

    def _fix_image(self, content: str) -> str:
        """修复图片标签样式"""
        pq = PyQuery(content)
        imgs = pq("img")
        if len(imgs) == 0:
            print("No images found in content")
            return content
        for line in imgs.items():
            link = """<img alt="{}" src="{}" />""".format(
                line.attr("alt"), line.attr("src")
            )
            figure = self._gen_css("figure", link, line.attr("alt"))
            content = content.replace(link, figure)
        return content

    def _format_fix(self, content: str) -> str:
        """修复其他格式问题"""
        content = content.replace("</li>", "</li>\n<p></p>")
        content = content.replace("<pre class=\"codehilite\">",
                                  self._gen_css("code"))
        return content

    def update_image_urls(self, content: str, uploaded_images: Dict) -> str:
        """更新内容中的图片URL"""
        content_copy = content
        for image, meta in uploaded_images.items():
            content_copy = content_copy.replace(f"({image})", f"({meta[1]})")
        return content_copy

    def get_thumbnail_id(self, uploaded_images: Dict) -> Optional[str]:
        """获取缩略图ID"""
        if uploaded_images:
            return list(uploaded_images.values())[0][0]
        return None

    def _save_debug_html(self, content: str, debug_file: str) -> str:
        """保存 HTML 到调试文件

        Args:
            content: 生成的 HTML 内容

        Returns:
            保存的文件路径
        """
        if not self.debug:
            return ""

        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = os.path.join(
            self.debug_dir, f"wx_html_{timestamp}_{debug_file}.html")

        # 添加基本的 HTML 结构和编码
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>WeChat HTML Preview - {timestamp}</title>
</head>
<body>
{content}
</body>
</html>"""

        # 保存文件
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(full_html)

        print(f"\nDebug HTML saved to: {debug_file}")
        return debug_file
