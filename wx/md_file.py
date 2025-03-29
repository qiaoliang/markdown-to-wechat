from dataclasses import dataclass
from dataclasses import dataclass, field
import os
from typing import Dict, Optional, List, Tuple
import re
import urllib.request
import time


@dataclass
class ImageReference:
    """Image reference information class for storing URL and path information"""

    url_in_text: str  # URL in markdown
    original_path: str  # Original path of the image before download
    target_path: str = ""  # Target path of the image after download
    existed: bool = True  # Whether the image exists locally
    external: bool = False  # Whether the image is external from web


def download_image(img_url, source_dir):
    """Download image from URL and save to assets directory"""
    # Create assets directory if it doesn't exist
    assets_dir = os.path.join(source_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    resource = urllib.request.urlopen(img_url)
    # Get file extension from URL or default to .png
    file_ext = os.path.splitext(img_url.split("/")[-1])[1]
    if not file_ext:
        file_ext = ".png"
    # Generate a unique filename using timestamp
    timestamp = int(time.time())
    name = f"image_{timestamp}{file_ext}"
    f_name = os.path.join(assets_dir, name)
    with open(f_name, "wb") as f:
        f.write(resource.read())
    return f_name


class MarkdownBody:
    """Markdown body information class for storing body content"""

    body_text: str = ""
    __image_Refs: List[ImageReference] = field(default_factory=list)

    def __init__(self, source_dir: str, body_text: str):
        self.source_dir = source_dir
        self.body_text = body_text
        self.__image_Refs = []  # Initialize as an empty list
        self.get_imgRefs()

    def get_imgRefs(self) -> List[ImageReference]:
        if self.__image_Refs:
            return self.__image_Refs
        img_links = re.findall(r"\!\[.*?\]\((.*?)\)", self.body_text)
        for link in img_links:
            img_existed = False
            local_path = ""
            external = link.startswith("http")
            if not external:
                local_path = os.path.abspath(
                    os.path.join(self.source_dir, link.lstrip("./"))
                )
                if os.path.exists(local_path):
                    img_existed = True
                else:
                    img_existed = False
            self.__image_Refs.append(
                ImageReference(
                    url_in_text=link,
                    original_path=local_path,
                    existed=img_existed,
                    external=external,
                )
            )
        return self.__image_Refs


@dataclass
class MarkdownHeader:
    """Markdown header information class for storing front matter metadata"""

    header_text: str = ""
    title: str = ""
    date: str = ""  # 文章发布日期
    keywords: List[str] = field(default_factory=list)  # 文章关键词
    description: str = ""  # 文章描述
    tags: List[str] = field(default_factory=list)  # 文章标签
    categories: List[str] = field(default_factory=list)  # 文章分类
    banner: str = ""  # 文章banner
    author: str = ""  # 文章作者
    draft: bool = True  # 是否为草稿
    gen_cover: bool = False  # 是否生成封面
    subtitle: str = ""  # 文章副标题
    source_dir: str = ""  # markdown文件所在目录
    banner_imgRef: Optional[ImageReference] = None
    SOURCE_URL: str = ""  # 文章来源URL

    def get_banner_imgRef(self) -> ImageReference:
        if (
            self.banner_imgRef is not None
        ):  # 如果banner_imgRef已经初始化存在，则直接返回
            return self.banner_imgRef
        banner_existed = False
        external = False
        # 确保有banner。如果banner为空，则使用网络随机图片作为默认banner
        if not self.banner:
            self.banner = "https://picsum.photos/900/300"

        if self.banner.startswith("http"):  # 如果banner是网络图片，则设置external为True
            external = True
        # 如果banner是本地图片，则设置banner_existed为True
        elif os.path.exists(os.path.join(self.source_dir, self.banner)):
            banner_existed = True
        self.banner_imgRef = ImageReference(
            url_in_text=self.banner,
            original_path=os.path.abspath(
                os.path.join(self.source_dir, self.banner)),
            existed=banner_existed,
            external=external,
        )
        return self.banner_imgRef

    @staticmethod
    def extract_header(source_dir: str, header_content: str) -> "MarkdownHeader":
        header = MarkdownHeader()
        # Store raw header text
        header.source_dir = source_dir
        header.header_text = header_content

        # Parse each line
        for line in header_content.strip().split("\n"):
            line = line.strip()
            if not line or line == "+++":
                continue

            # Match one field per line
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"')

                if key == "title":
                    header.title = value
                elif key == "date":
                    header.date = value
                elif key == "subtitle":
                    header.subtitle = value
                elif key == "gen_cover":
                    if value.lower() in ["true", "yes", "y"]:
                        header.gen_cover = True
                    else:
                        header.gen_cover = False
                elif key == "keywords":
                    header.keywords = [
                        k.strip(" \"'") for k in value.strip("[]").split(",")
                    ]
                elif key == "description":
                    header.description = value
                elif key == "tags":
                    header.tags = [
                        t.strip(" \"'") for t in value.strip("[]").split(",")
                    ]
                elif key == "categories":
                    header.categories = [
                        c.strip(" \"'") for c in value.strip("[]").split(",")
                    ]
                elif key == "banner":
                    header.banner = value
                elif key == "author":
                    header.author = value
                elif key == "draft":
                    if value.lower() in ["true", "yes", "y"]:
                        header.draft = True
                    else:
                        header.draft = False
        if header.subtitle == "":
            header.subtitle = header.title
        header.get_banner_imgRef()
        return header


@dataclass
class MarkdownFile:
    """Markdown file class for storing file information and image references"""

    source_dir: str = ""
    base_name: str = ""  # file name without path
    abs_path: str = ""  # absolute path to the md file
    content: str = ""  # content of the file
    image_pairs: List[ImageReference] = field(
        default_factory=list)  # image in the file
    header: MarkdownHeader = field(
        default_factory=MarkdownHeader)  # header information
    # body content of the file
    body: MarkdownBody = field(default_factory=MarkdownBody)
    web_images_downloaded: bool = False
    image_uploaded: bool = False
    uploaded_images: Dict[str, List[str]] = field(default_factory=dict)

    def __init__(self, source_dir: str, md_file_name: str):
        self.source_dir = source_dir
        md_file_path = os.path.abspath(os.path.join(source_dir, md_file_name))
        if not os.path.exists(md_file_path):
            raise FileNotFoundError(f"File not found: {md_file_path}")
        self.base_name = os.path.basename(md_file_path)
        self.abs_path = os.path.abspath(md_file_path)
        self.image_pairs = []  # Initialize as an empty list
        self.uploaded_images = {}  # Initialize as an empty dict
        self.__load_content()

    def get_imgRefs(self) -> List[ImageReference]:
        if self.image_pairs:  # 如果image_pairs已经初始化，则直接返回
            return self.image_pairs
        self.image_pairs = self.body.get_imgRefs()
        banner_ref = self.header.get_banner_imgRef()
        self.image_pairs.insert(0, banner_ref)  # 将banner插入到image_pairs的头部
        if len(self.image_pairs) == 0:
            raise ValueError("No image links found in the header and body")
        return self.image_pairs

    def __extract_header_and_body(self, content: str) -> Tuple[str, str]:
        self.image_pairs = []
        wechat_match = re.search(r"^\+\+\+(.*?)\+\+\+", content, re.DOTALL)
        if not wechat_match:
            raise ValueError("No header found in the content")
        header_text = wechat_match.group(1).strip()
        self.header = MarkdownHeader.extract_header(
            self.source_dir, header_text)

        body_text = content[wechat_match.end():].strip()
        self.body = MarkdownBody(self.source_dir, body_text)
        self.image_pairs = self.get_imgRefs()

    def __load_content(self):
        # Read content from file if not provided
        with open(self.abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.content = content
        self.__extract_header_and_body(content)
        return self

    def find_broken_img_links(self) -> List[ImageReference]:
        ret = []
        if not self.image_pairs:  # Ensure image_pairs is initialized and not empty
            self.get_imgRefs()  # Populate image_pairs if empty
        for imgRef in self.image_pairs:
            if not imgRef.external and not imgRef.existed:
                ret.append(imgRef)
        if not ret:
            return []
        print("以下图片未找到:")
        for imgRef in ret:
            print(imgRef.url_in_text, imgRef.original_path)
        return ret

    @staticmethod
    def extract(source_dir: str, file_path: str) -> "MarkdownFile":
        """Extract markdown file content without downloading images"""
        file = MarkdownFile(source_dir, file_path)
        return file

    def download_image_from_web(self):
        """Download image from web and save to assets directory"""
        imgRefs = [imgRef for imgRef in self.image_pairs if imgRef.external]
        for imgRef in imgRefs:
            f_name = ""
            content = None
            try:
                resource = urllib.request.urlopen(imgRef.url_in_text)
                content = resource.read()
            except Exception as e:
                print(
                    f"Error downloading image {imgRef.url_in_text} from web: {e}")
                continue
            if content:
                imgRef.existed = True
                # Create assets directory if it doesn't exist
                assets_dir = os.path.join(self.source_dir, "assets")
                os.makedirs(assets_dir, exist_ok=True)

                # Get file extension from URL or default to .png
                file_ext = os.path.splitext(
                    imgRef.url_in_text.split("/")[-1])[1]
                if not file_ext:
                    file_ext = ".png"

                # Generate a unique filename using timestamp
                timestamp = int(time.time())
                name = f"image_{timestamp}{file_ext}"
                f_name = os.path.join(assets_dir, name)

                with open(f_name, "wb") as f:
                    f.write(content)
                    imgRef.original_path = f_name
            else:
                imgRef.existed = False

    def use_temp_img_for_unavailable_img(self):
        """Use temp image for unavailable image"""
        for imgRef in self.image_pairs:
            if not imgRef.existed:
                imgRef.original_path = f"assets/img_unavailable.png"
                imgRef.existed = True


@dataclass
class OrgImageInfo:
    """Image link information class for storing URL and path information"""

    url_in_text: str  # Original URL as it appears in the markdown text
    abs_path: str  # Resolved absolute path to the image file
    exists: bool = False  # Whether the image file exists
    is_frontmatter: bool = False  # Whether the image is referenced in frontmatter
