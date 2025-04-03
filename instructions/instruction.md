# Project overview

You are building a markdown tools, where users can chack the format of markdown files in a source direcotry, and upload images which are referenced in markdown files and publish the markdown file as wechat article to wechat platform. Also users can check the format based on the requirement of HUGO, a blog writer tools, and build the html file for the hugo articles.

You will be using python3.12, markdown package and so on.
I
# Core functionalities

1. users can run command to deal with markdown file. the command is like the following formmat: 'python -m wx.sync -src /path/to/your/markdown/source/dirs -a check -t wx'.
    1. Param '-a' could be as '--act', and '-t' could be as '--type'. 
    2. Param value for '-a' could be 'check' or 'post'.
    3. Param value for '-t' could be 'wx' or 'hugo'. 
2.  Given the value of '-t' is 'wx', 
    1. When the value of '-a' is 'check',  then the application will check whether all images in a markdown file are avaliable. If not, inform the users which file with which images is unavaliable. 
    2. when the value of '-a' is 'post', then the application firstly will check the format for markdown files as 2.1, and if everything is ok, then the application will publish all the articles to wx platform using wx_client.py.
3.  Given the value of '-t' is 'hugo',
    1. When the value of '-a' is 'check', then the application will check whether all format of markdown file is suitable with Hugo. If not, notice the users the format deails.
    1. When the value of '-a' is 'post', then the application firstly will check whether all format of markdown file is suitable with Hugo. And if everything is ok, the application will publish all the articles with images which are referenced to the default location. 'Publish' means two things, one is to move all md file to a specific location, the other is to move all images related with those md files to another specific location. Both locations will be gotten from envrionment varables.

4. 对front format 进行检查，使用 hugo 的front format格式。 
   	- 可以使用 a) (key="{value}") 或 b) (key: value）的格式。但是不能同时使用a)或b). 如果md_file 同时使用了,那么修改 md_file 的源文件，使其使用 a) 格式。 
   	- 自动删除 markdown 源文件中的空行
   	- 根据 hugo front format ，如果key 有缺失，则修改 md_file 的源文件，补全它。注意：应该提示用户，哪个源文件，做了那些修改。
   	- 以下是 Key value 补全的规则：
        - 如果 title 为空，则总结文章body 部分的内容概要，为文章总结一个title, 并且这个title 在突出文章重点的同时，还要提升读者的阅读欲望。
        - subtitle 和 discrption 有其中之一就可以。它们两个是等效的Key。
        -  subtitle 或 discrption 为空时，你需要 (a)使用一句话总结这些内容(必须贴切，不超过50个字)
    - 当 tags为空时，你需要总结出三个关键词 tag1, tag2 and tag3。输出格式如下：tags=["{tag1}","{tag2}", "{tag3}"]
    - 当没有 banner，或 banner 为空时，要设置为 ‘https://picsum.photos/id/{value}/900/300.jpg’. 其中， {value} 是一个 1~100之间的随机数字。
    - 当 categories 为空时，需要总结出文章属于下面哪个分类，只能选一个，类似于 [个人观点，实践总结，方法论，AI编程,软件工程,工程效能，人工智能]。如果以上分类都不合适，可以再设计一个新的分类。但你需要记住这些分类，分类的总数不能多于10个。
    - 当 keywords 为空时，需要在网络上找到一些有利于 SEO ，且与文章内容相关的关键字。关键字的数量不超过20个。对应的格式如下：keywords=["keyword1","keyword2","keyword3"]


# Documentation 

Front Formatter of Hugo can be used for the markdown file with wechat article.

## Hugo 的Archetypes 可以参考这个文档 https://gohugo.io/content-management/archetypes/

Front Formatter  EXAMPLE is like following. It may have more attributes besides the follows:

```
+++
date = '{{ .Date }}'
draft = true
title = '{{ replace .File.ContentBaseName `-` ` ` | title }}'
+++

```

## Documentation for wechat api. We use WeRobot framework to conmunicate with wechet platform. The API document  is here: https://github.com/offu/WeRoBot/blob/master/docs/client.rst


CODE EXAMPLE
```javascript
// Example usage
async function main(){
const post: RedditPost = {
title: "Need help with my new laptop",
content: "I just bought a new laptop and I'm havingtrouble setting it up. Any advice?"
};
```

# Current file structure

```
markdown-to-wechat
.
├── README.md
├── assets
│   ├── code.tmpl
│   ├── figure.tmpl
│   ├── header.tmpl
│   ├── img_unavailable.png
│   ├── link.tmpl
│   ├── numb.tmpl
│   ├── para.tmpl
│   ├── ref_header.tmpl
│   ├── ref_link.tmpl
│   ├── sub.tmpl
│   └── sub_num.tmpl
├── dist
│   ├── wx-0.1.0-py3-none-any.whl
│   └── wx-0.1.0.tar.gz
├── instructions
│   └── instructions-v1.md
├── poetry.lock
├── pyproject.toml
├── testdata
│   ├── Cache.bin
│   ├── a_template.md
│   └── assets
├── tests
│   ├── __pycache__
│   ├── integration
│   ├── test_cli.py
│   ├── test_image_processor.py
│   ├── test_md_file.py
│   ├── test_wx_cache.py
│   ├── test_wx_htmler.py
│   └── test_wx_publisher.py
└── wx
    ├── __init__.py
    ├── __pycache__
    ├── cli.py
    ├── image_processor.py
    ├── md_file.py
    ├── wx_cache.py
    ├── wx_client.py
    ├── wx_htmler.py
    └── wx_publisher.py
```

# 所用的技术框架

 1. 使用 pytest 做测试框架
 2. 使用 poetry 做项目构建管理
 3. 使用 markdown package 做 markdown 到 html 的转换
 4. 使用 pickle package 做存储管理
 5. 使用 WeRobot 框架与微信公众号平台通信

# 项目管理

- 所有功能实现应参考 instructions/Instruction.md
- 所有API端点及其请求/响应格式参考 instructions/Documentation.md
- 确保新代码符合定义的里程碑
- 遵循已建立的数据库架构
- 考虑指标中定义的成本优化
- 保持与现有组件的一致性