import pytest
from wx.openrouter_service import OpenRouterService
from unittest.mock import MagicMock, patch


@pytest.fixture
def sample_article_content():
    return """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Understanding Python's Async IO
Python's asynchronous IO system is a powerful way to handle concurrent operations.
This article explains the core concepts and best practices for using async/await in Python.

## Key Concepts
- Coroutines
- Event Loop
- Async/Await Syntax

## Benefits
1. Better performance for IO-bound operations
2. Clean and readable code
3. Efficient resource utilization"""


@pytest.fixture
def mock_openai_response():
    class MockResponse:
        def __init__(self):
            self.choices = [
                type('Choice', (), {
                    'message': type('Message', (), {
                        'content': "Understanding Async IO in Python: A Comprehensive Guide"
                    })
                })
            ]
    return MockResponse()


@pytest.fixture
def openrouter_service(monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test_key')
    return OpenRouterService()


@pytest.fixture
def mock_openai():
    with patch('wx.openrouter_service.OpenAI') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


def test_init_without_api_key(monkeypatch):
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    with pytest.raises(ValueError) as exc:
        OpenRouterService()
    assert "OPENROUTER_API_KEY environment variable is not set" in str(
        exc.value)


def test_summarize_for_title(mock_openai):
    """Test title generation with mocked OpenAI client."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Python异步IO编程指南"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Understanding Python's Async IO
Python's asynchronous IO system is a powerful way to handle concurrent operations.
This article explains the core concepts and best practices for using async/await in Python.

## Key Concepts
- Coroutines
- Event Loop
- Async/Await Syntax"""

    service = OpenRouterService()
    title = service.summarize_for_title(content)

    # Verify the title
    assert isinstance(title, str)
    assert len(title) <= 100  # Title should be within length limit

    # Verify OpenAI client was called correctly
    mock_openai.chat.completions.create.assert_called_once()
    call_args = mock_openai.chat.completions.create.call_args[1]
    assert call_args['model'] == "deepseek/deepseek-v3-base:free"
    assert len(call_args['messages']) == 2
    assert call_args['messages'][0]['role'] == "system"
    assert "标题生成器" in call_args['messages'][0]['content']


def test_summarize_for_subtitle(mock_openai):
    """Test subtitle generation with mocked OpenAI client."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="深入解析Python异步IO编程。"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Understanding Python's Async IO
Python's asynchronous IO system is a powerful way to handle concurrent operations.
This article explains the core concepts and best practices for using async/await in Python.

## Key Concepts
- Coroutines
- Event Loop
- Async/Await Syntax"""

    service = OpenRouterService()
    subtitle = service.summarize_for_subtitle(content)

    # Verify the subtitle
    assert isinstance(subtitle, str)
    assert len(subtitle) <= 50  # Subtitle should be within length limit
    assert subtitle.endswith('。')  # Should end with period

    # Verify OpenAI client was called correctly
    mock_openai.chat.completions.create.assert_called_once()
    call_args = mock_openai.chat.completions.create.call_args[1]
    assert call_args['model'] == "deepseek/deepseek-v3-base:free"
    assert len(call_args['messages']) == 2
    assert call_args['messages'][0]['role'] == "system"
    assert "副标题生成器" in call_args['messages'][0]['content']


def test_summarize_for_subtitle_long_input(mock_openai):
    """Test subtitle generation with long input content."""
    # Setup mock response with a long subtitle
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(
            content="这是一个非常长的副标题，它超过了五十个字符的最大允许长度限制，需要被截断。bd218f28-d23d-4b2d-8b84-528c347c7501bd218f28-d23d-4b2d-8b84-528c347c7501"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content with multiple paragraphs
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Understanding Python's Async IO
Python's asynchronous IO system is a powerful way to handle concurrent operations.
This article explains the core concepts and best practices for using async/await in Python.

## Key Concepts
- Coroutines
- Event Loop
- Async/Await Syntax

## Benefits
1. Better performance for IO-bound operations
2. Clean and readable code
3. Efficient resource utilization

## Advanced Topics
- Error handling in async code
- Async context managers
- Task cancellation
- Debugging async applications"""

    service = OpenRouterService()
    subtitle = service.summarize_for_subtitle(content)

    # Verify the subtitle
    assert isinstance(subtitle, str)
    assert len(subtitle) <= 50  # Should be truncated to fit length limit
    assert subtitle.endswith("...")  # Should end with ellipsis if truncated


def test_generate_tags(mock_openai):
    """Test tag generation with mocked OpenAI client."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(
            content="python-async\nconcurrency\nio-operations"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Understanding Python's Async IO
Python's asynchronous IO system is a powerful way to handle concurrent operations.
This article explains the core concepts and best practices for using async/await in Python.

## Key Concepts
- Coroutines
- Event Loop
- Async/Await Syntax"""

    service = OpenRouterService()
    tags = service.generate_tags(content)

    # Verify the tags
    assert isinstance(tags, list)
    assert len(tags) == 3  # Should always return exactly 3 tags
    assert all(isinstance(tag, str)
               for tag in tags)  # All tags should be strings
    assert all(tag.strip() == tag for tag in tags)  # Tags should be stripped
    assert all('"' not in tag for tag in tags)  # No quotes in tags
    # No brackets
    assert all('[' not in tag and ']' not in tag for tag in tags)
    # Only alphanumeric and hyphens
    assert all(all(c.isalnum() or c == '-' for c in tag) for tag in tags)

    # Verify OpenAI client was called correctly
    mock_openai.chat.completions.create.assert_called_once()
    call_args = mock_openai.chat.completions.create.call_args[1]
    assert call_args['model'] == "deepseek/deepseek-v3-base:free"
    assert len(call_args['messages']) == 1
    assert "标签生成器" in call_args['messages'][0]['content']


def test_generate_tags_insufficient_response(mock_openai):
    """Test tag generation when API returns fewer than 3 tags."""
    # Setup mock response with only one tag
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="python-web"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Understanding Python
A basic guide to Python programming."""

    service = OpenRouterService()
    tags = service.generate_tags(content)

    # Verify we still get exactly 3 tags
    assert len(tags) == 3
    assert tags[0] == "python-web"  # First tag from API
    assert tags[1] == "tag-2"  # Generated tag
    assert tags[2] == "tag-3"  # Generated tag


def test_generate_tags_excess_response(mock_openai):
    """Test tag generation when API returns more than 3 tags."""
    # Setup mock response with 5 tags
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(
            content="python-web\nweb-dev\nbackend\ndjango\nflask"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Python Web Development"""

    service = OpenRouterService()
    tags = service.generate_tags(content)

    # Verify we get exactly 3 tags
    assert len(tags) == 3
    assert tags == ["python-web", "web-dev",
                    "backend"]  # Should keep first 3 tags


def test_suggest_category(mock_openai):
    """Test category suggestion with mocked OpenAI client."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="软件工程"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content about software engineering
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Best Practices in Software Design
This article discusses SOLID principles, design patterns,
and other best practices in software engineering."""

    service = OpenRouterService()
    category = service.suggest_category(content)

    # Verify the category
    assert isinstance(category, str)
    assert category in ["个人观点", "实用总结", "方法论",
                        "AI编程", "软件工程", "工程效率",
                        "人工智能"]
    assert category == "软件工程"  # Should match the mock response

    # Verify OpenAI client was called correctly
    mock_openai.chat.completions.create.assert_called_once()
    call_args = mock_openai.chat.completions.create.call_args[1]
    assert call_args['model'] == "deepseek/deepseek-v3-base:free"
    assert len(call_args['messages']) == 1
    assert "内容分类器" in call_args['messages'][0]['content']


def test_suggest_category_new_category(mock_openai):
    """Test category suggestion with a new category."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="云原生开发"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content about cloud native development
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Understanding Kubernetes and Cloud Native Development
This article discusses cloud native development principles and Kubernetes basics."""

    service = OpenRouterService()
    category = service.suggest_category(content)

    # Verify the category
    assert isinstance(category, str)
    assert len(category.split()) <= 3  # Should be at most 3 words
    assert category == "云原生开发"  # Should match the mock response


def test_suggest_category_empty_content(mock_openai):
    """Test category suggestion with empty content."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="个人观点"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    service = OpenRouterService()
    category = service.suggest_category("")

    # Should default to a safe category for empty content
    assert category == "个人观点"


def test_suggest_category_max_categories(mock_openai):
    """Test category suggestion respects maximum category limit."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="软件工程"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    service = OpenRouterService()

    # Simulate having 10 existing categories
    existing_categories = [
        "个人观点", "实用总结", "方法论",
        "AI编程", "软件工程", "工程效率",
        "人工智能", "数据科学", "Web开发",
        "移动开发"
    ]

    # When we have max categories, should return one of existing categories
    category = service.suggest_category("Some content", existing_categories)
    assert category in existing_categories


def test_generate_seo_keywords(mock_openai):
    """Test SEO keyword generation with mocked OpenAI client."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(
            content="Python编程, 异步IO, 并发编程, 协程, 事件循环"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Understanding Python's Async IO
Python's asynchronous IO system is a powerful way to handle concurrent operations.
This article explains the core concepts and best practices for using async/await in Python.

## Key Concepts
- Coroutines
- Event Loop
- Async/Await Syntax"""

    service = OpenRouterService()
    keywords = service.generate_seo_keywords(content)

    # Verify the keywords
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert len(keywords) <= 20  # Should not exceed 20 keywords
    assert all(isinstance(kw, str)
               for kw in keywords)  # All keywords should be strings
    # Each keyword max 3 words
    assert all(len(kw.split()) <= 3 for kw in keywords)

    # Verify OpenAI client was called correctly
    mock_openai.chat.completions.create.assert_called_once()
    call_args = mock_openai.chat.completions.create.call_args[1]
    assert call_args['model'] == "deepseek/deepseek-v3-base:free"
    assert len(call_args['messages']) == 2
    assert "SEO关键词" in call_args['messages'][0]['content']


def test_generate_seo_keywords_empty_content(mock_openai):
    """Test SEO keyword generation with empty content."""
    service = OpenRouterService()
    keywords = service.generate_seo_keywords("")

    # Should return empty list for empty content
    assert isinstance(keywords, list)
    assert len(keywords) == 0


def test_generate_seo_keywords_long_response(mock_openai):
    """Test SEO keyword generation with long response."""
    # Setup mock response with many keywords
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(
            content="Python编程, 异步IO, 并发编程, 协程, 事件循环, 异步编程, Python开发, "
            "软件工程, 最佳实践, 性能优化, IO密集型, 代码整洁, 资源利用, "
            "异步开发, Python异步, 开发技巧, 系统架构, 编程范式, 技术选型, "
            "架构设计, 编程思想, 开发效率"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Understanding Python's Async IO
A comprehensive guide to async/await in Python."""

    service = OpenRouterService()
    keywords = service.generate_seo_keywords(content)

    # Verify we get at most 20 keywords
    assert isinstance(keywords, list)
    assert len(keywords) <= 20
    assert all(isinstance(kw, str) for kw in keywords)
    assert all(len(kw.split()) <= 3 for kw in keywords)
