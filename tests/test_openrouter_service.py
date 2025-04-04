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
        MagicMock(message=MagicMock(
            content="Understanding Async IO in Python: A Comprehensive Guide"))
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
    assert "Python" in title  # Should contain relevant keyword

    # Verify OpenAI client was called correctly
    mock_openai.chat.completions.create.assert_called_once()
    call_args = mock_openai.chat.completions.create.call_args[1]
    assert call_args['model'] == "deepseek/deepseek-v3-base:free"
    assert len(call_args['messages']) == 2
    assert call_args['messages'][0]['role'] == "system"
    assert "title generator" in call_args['messages'][0]['content'].lower()
    assert call_args['max_tokens'] == 20  # Should use limited tokens for title


def test_summarize_for_subtitle(mock_openai):
    """Test subtitle generation with mocked OpenAI client."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(
            content="A guide to Python's async/await system"))
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
    assert "Python" in subtitle  # Should contain relevant keyword

    # Verify OpenAI client was called correctly
    mock_openai.chat.completions.create.assert_called_once()
    call_args = mock_openai.chat.completions.create.call_args[1]
    assert call_args['model'] == "deepseek/deepseek-v3-base:free"
    assert len(call_args['messages']) == 2
    assert call_args['messages'][0]['role'] == "system"
    assert "subtitle generator" in call_args['messages'][0]['content'].lower()
    # Should use limited tokens for subtitle
    assert call_args['max_tokens'] == 15


def test_summarize_for_subtitle_long_input(mock_openai):
    """Test subtitle generation with long input content."""
    # Setup mock response with a long subtitle
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(
            content="This is a very long subtitle that exceeds the maximum allowed length of fifty characters"))
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
            content="python-async, concurrency, io-operations"))
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

    # Verify OpenAI client was called correctly
    mock_openai.chat.completions.create.assert_called_once()
    call_args = mock_openai.chat.completions.create.call_args[1]
    assert call_args['model'] == "deepseek/deepseek-v3-base:free"
    assert len(call_args['messages']) == 2
    assert call_args['messages'][0]['role'] == "system"
    assert "tag generator" in call_args['messages'][0]['content'].lower()
    assert call_args['max_tokens'] == 20  # Should use limited tokens for tags


def test_generate_tags_insufficient_response(mock_openai):
    """Test tag generation when API returns fewer than 3 tags."""
    # Setup mock response with only one tag
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="python"))
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
    assert tags[0] == "python"  # First tag from API
    assert "Understanding Python" in tags[1]  # Second tag from content
    assert tags[2].startswith("topic-")  # Third tag is generic


def test_generate_tags_excess_response(mock_openai):
    """Test tag generation when API returns more than 3 tags."""
    # Setup mock response with 5 tags
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(
            content="python, async, io, concurrency, performance"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Python Performance Tips"""

    service = OpenRouterService()
    tags = service.generate_tags(content)

    # Verify we get exactly 3 tags
    assert len(tags) == 3
    assert tags == ["python", "async", "io"]  # Should keep first 3 tags


def test_suggest_category(mock_openai):
    """Test category suggestion with mocked OpenAI client."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(
            content="Software Engineering"))
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
    assert category in ["Personal Opinion", "Practical Summary", "Methodology",
                        "AI Programming", "Software Engineering", "Engineering Efficiency",
                        "Artificial Intelligence"]
    assert category == "Software Engineering"  # Should match the mock response

    # Verify OpenAI client was called correctly
    mock_openai.chat.completions.create.assert_called_once()
    call_args = mock_openai.chat.completions.create.call_args[1]
    assert call_args['model'] == "deepseek/deepseek-v3-base:free"
    assert len(call_args['messages']) == 2
    assert call_args['messages'][0]['role'] == "system"
    assert "category suggester" in call_args['messages'][0]['content'].lower()


def test_suggest_category_new_category(mock_openai):
    """Test category suggestion when content doesn't match predefined categories."""
    # Setup mock response for a new category
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(
            content="Data Science"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    # Test content about data science
    content = """title=""
subtitle=""
tags=[]
categories=[]
keywords=[]
---
# Introduction to Data Science
This article covers the basics of data science,
including statistics, data analysis, and visualization."""

    service = OpenRouterService()
    category = service.suggest_category(content)

    # Verify the category
    assert isinstance(category, str)
    assert category == "Data Science"  # Should accept the new category
    assert len(category) > 0
    assert all(c.isalnum() or c.isspace()
               for c in category)  # Only allow letters, numbers, and spaces


def test_suggest_category_empty_content(mock_openai):
    """Test category suggestion with empty content."""
    service = OpenRouterService()
    category = service.suggest_category("")

    # Should default to a safe category for empty content
    assert category == "Personal Opinion"


def test_suggest_category_max_categories(mock_openai):
    """Test category suggestion respects maximum category limit."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(
            content="New Category"))
    ]
    mock_openai.chat.completions.create.return_value = mock_response

    service = OpenRouterService()

    # Simulate having 10 existing categories
    existing_categories = [
        "Personal Opinion", "Practical Summary", "Methodology",
        "AI Programming", "Software Engineering", "Engineering Efficiency",
        "Artificial Intelligence", "Data Science", "Web Development",
        "Mobile Development"
    ]

    # When we have max categories, should return one of existing categories
    category = service.suggest_category("Some content", existing_categories)
    assert category in existing_categories
