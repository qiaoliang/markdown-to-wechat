# Markdown Toolset Project Prompt

## Project Overview
Develop a Markdown toolset using Python 3.12. The tool allows users to perform operations on Markdown files, including format checking, image uploading, and publishing to the WeChat platform or generating HTML files for Hugo articles.

## Core Functionalities

### Command - Line Interface
- Users can run commands in the following format to handle Markdown files:
  - `python -m wx.sync -src /path/to/your/markdown/source/dirs -a <action> -t <type>`
  - `-a` (alias `--act`): Valid values are `check` or `post`.
  - `-t` (alias `--type`): Valid values are `wx` or `hugo`.

### Operations for WeChat (`-t wx`)
- **`-a check`**:
  - Check if all images referenced in Markdown files are available.
  - If any images are unavailable, inform the user about the specific file and the missing images.
- **`-a post`**:
  - First, perform the same image availability check as in the `check` action.
  - If all checks pass, publish all articles to the WeChat platform using `wx_client.py`.

### Operations for Hugo (`-t hugo`)
- **`-a check`**:
  - Check if the format of all Markdown files is suitable for Hugo.
  - If there are format issues, notify the user with detailed information.
- **`-a post`**:
  - First, perform the format suitability check.
  - If all checks pass, publish all articles along with their referenced images:
    - Get the target home directory from environment variable `HUGO_TARGET_HOME`
    - Copy Markdown files to `{HUGO_TARGET_HOME}/content/blog`
    - Copy related images to `{HUGO_TARGET_HOME}/static/img/blog`
    - Notify the user about the publishing results

### Front - Formatting for Hugo
- **Format Consistency**:
  - Markdown files should use either `(key="{value}")` or `(key: value)` format for front matter, but not both.
  - If a file uses both, modify the source file to use the `(key="{value}")` format.
- **Empty Line Removal**:
  - Automatically remove all empty lines from the Markdown source files.
- **Key Completion**:
  - **Title**:
    - If the `title` is empty, summarize the content of the article body to create a title that highlights the key points and attracts readers.
  - **Subtitle/Description**:
    - If either `subtitle` or `description` is missing, summarize the article content in a single sentence (no more than 50 characters).
  - **Tags**:
    - If `tags` are empty, summarize three keywords in the format `tags=["{tag1}","{tag2}", "{tag3}"]`.
  - **Banner**:
    - If `banner` is missing or empty, set it to `https://picsum.photos/id/{value}/900/300.jpg`, where `{value}` is a random number between 1 and 100.
  - **Categories**:
    - If `categories` are empty, assign the article to one of the following categories: [Personal Opinion, Practical Summary, Methodology, AI Programming, Software Engineering, Engineering Efficiency, Artificial Intelligence].
    - If none of these fit, create a new category, ensuring the total number of categories does not exceed 10.
  - **Keywords**:
    - If `keywords` are empty, find up to 20 SEO - friendly keywords related to the article content and format them as `keywords=["keyword1","keyword2","keyword3"]`.
    - Notify the user about which source file has been modified and what changes have been made.
  

## Technical Frameworks
- **Testing**: Use `pytest` as the testing framework, 不要使用 unittest package. 如果使用mock，请使用 pytest 提供的相关API。
- **Project Management**: Use `poetry` for project building and management.
- **Markdown Conversion**: Use the `markdown` package to convert Markdown to HTML.
- **Storage**: Use the `pickle` package for storage management.
- **WeChat Communication**: Use the WeRobot framework() to communicate with the WeChat official account platform.
- **OpenRouter**: Use openRouter and free LLM named `deepseek/deepseek-v3-base:free` to summarize doc for title, subtitle, and keyword and categary, find SEO keywords. Get the openRouter API Key from system environment variable 'OPENROUTER_API_KEY'. 

## Documentation
### **Hugo Front - Format**: The front - matter formatter for Hugo can be applied to Markdown files for WeChat articles. Refer to [Hugo's Archetypes documentation](https://gohugo.io/content-management/archetypes/) for more details.
### **WeChat API**: Use the WeRobot framework to communicate with the WeChat platform. Refer to the [WeRobot API documentation](https://github.com/offu/WeRoBot/blob/master/docs/client.rst) for API details.
### ** OpenRouter API**

We use OPENAI SDK format to use OpenRouter. the doc reference is  here: https://openrouter.ai/docs/quickstart.
the code example :

```
from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="<OPENROUTER_API_KEY>",
)

completion = client.chat.completions.create(
  extra_headers={
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  model="openai/gpt-4o",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)

print(completion.choices[0].message.content)

```

## Current File Structure
```
markdown-to-wechat
.
├── README.md
├── assets
│   ├── code.tmpl
│   ├── figure.tmpl
│   ├── header.tmpl
│   ├── img_unavailable.png
│   ├── link.tmpl
│   ├── numb.tmpl
│   ├── para.tmpl
│   ├── ref_header.tmpl
│   ├── ref_link.tmpl
│   ├── sub.tmpl
│   └── sub_num.tmpl
├── dist
│   ├── wx-0.1.0-py3-none-any.whl
│   └── wx-0.1.0.tar.gz
├── instructions
│   └── instructions-v1.md
├── poetry.lock
├── pyproject.toml
├── testdata
│   ├── Cache.bin
│   ├── a_template.md
│   └── assets
├── tests
│   ├── __pycache__
│   ├── integration
│   ├── test_cli.py
│   ├── test_image_processor.py
│   ├── test_md_file.py
│   ├── test_wx_cache.py
│   ├── test_wx_htmler.py
│   └── test_wx_publisher.py
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

## Hugo Operations

### Empty Line Removal
The empty line removal functionality ensures markdown files maintain a clean and consistent structure while preserving semantic meaning. The system follows these rules:

1. **Basic Rules**:
   - Remove multiple consecutive empty lines, keeping only one
   - Remove unnecessary empty lines at the start and end of the file
   - Preserve single empty lines between paragraphs
   - Preserve single empty lines before and after headers

2. **Special Cases**:
   - **Code Blocks**: Preserve all empty lines within code blocks
   - **Lists**: 
     - Keep single empty line between list items
     - Allow empty line between different list groups
   - **Front Matter**: 
     - Remove empty lines within front matter
     - Keep single empty line after front matter

3. **Integration**:
   - Empty line removal is integrated into the `HugoProcessor`
   - Runs after format standardization
   - Preserves front matter formatting

### Format Checking and Standardization
// ... existing code ...
