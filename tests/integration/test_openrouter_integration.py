import pytest
import os
from wx.openrouter_service import OpenRouterService


def check_openrouter_key():
    """Skip test if OPENROUTER_API_KEY is not set."""
    return pytest.mark.skipif(
        not os.getenv('OPENROUTER_API_KEY'),
        reason="OPENROUTER_API_KEY environment variable is not set"
    )


@check_openrouter_key()
def test_openrouter_title_generation():
    """Integration test for title generation using real OpenRouter API.

    This test requires OPENROUTER_API_KEY environment variable to be set.
    """
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
3. Efficient resource utilization"""

    service = OpenRouterService()
    title = service.summarize_for_title(content)

    # Verify the generated title
    assert isinstance(title, str)
    assert len(title) > 0
    assert len(title) <= 100  # Title shouldn't be too long


@check_openrouter_key()
def test_openrouter_subtitle_generation():
    """Integration test for subtitle generation using real OpenRouter API.

    This test requires OPENROUTER_API_KEY environment variable to be set.
    """
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
3. Efficient resource utilization"""

    service = OpenRouterService()
    subtitle = service.summarize_for_subtitle(content)

    # Verify the subtitle
    assert isinstance(subtitle, str)
    assert len(subtitle) > 0
    assert len(subtitle) <= 50  # Subtitle must be within length limit

    # The subtitle should be a complete sentence
    assert subtitle.endswith('。') or subtitle.endswith('...'), \
        f"Subtitle '{subtitle}' should end with proper punctuation (。 or ...)"


@check_openrouter_key()
def test_openrouter_tag_generation():
    """Integration test for tag generation using real OpenRouter API.

    This test requires OPENROUTER_API_KEY environment variable to be set.
    """
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
3. Efficient resource utilization"""

    service = OpenRouterService()
    tags = service.generate_tags(content)

    # Verify we get exactly 3 tags
    assert isinstance(tags, list)
    assert len(tags) == 3

    # Verify each tag is a valid string
    for tag in tags:
        assert isinstance(tag, str)
        assert len(tag) > 0
        assert ' ' not in tag  # No spaces allowed in tags
        # Only allow alphanumeric and hyphen
        assert all(c.isalnum() or c == '-' for c in tag)

    # Tags should be unique
    assert len(set(tags)) == 3, "All tags should be unique"

    # Print tags for manual inspection
    print(f"\nGenerated tags: {tags}")


@check_openrouter_key()
def test_openrouter_category_suggestion():
    """Integration test for category suggestion using real OpenRouter API.

    This test requires OPENROUTER_API_KEY environment variable to be set.
    """
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
3. Efficient resource utilization"""

    service = OpenRouterService()

    # Test with no existing categories (should prefer predefined ones)
    category = service.suggest_category(content)

    # Verify the category
    assert isinstance(category, str)
    assert len(category) > 0
    # Category should be one of predefined ones or a reasonable new one
    predefined = ["个人观点", "实用总结", "方法论",
                  "AI编程", "软件工程", "工程效率",
                  "人工智能"]
    if category not in predefined:
        # If not predefined, should be reasonable length
        words = category.split()
        assert len(
            words) <= 3, f"Category '{category}' should be at most 3 words"
        # Should only contain Chinese characters, letters, numbers, and spaces
        assert all(c.isalnum() or c.isspace() or '\u4e00' <= c <= '\u9fff' for c in category), \
            f"Category '{category}' should only contain Chinese characters, letters, numbers, and spaces"

    # Test with maximum categories (should only use existing ones)
    existing_categories = predefined + \
        ["Web开发", "移动开发", "数据科学"]
    category_max = service.suggest_category(content, existing_categories)
    assert category_max in existing_categories, \
        f"Category '{category_max}' should be one of existing categories when at max limit"

    # Print categories for manual inspection
    print(f"\nGenerated category (no existing): {category}")
    print(f"Generated category (max limit): {category_max}")


@check_openrouter_key()
def test_openrouter_seo_keywords():
    """Integration test for SEO keyword generation using real OpenRouter API.

    This test requires OPENROUTER_API_KEY environment variable to be set.
    """
    service = OpenRouterService()
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
- Task Management
- Error Handling

## Benefits
- Improved performance for IO-bound operations
- Better resource utilization
- Clean and maintainable code
- Scalable application design"""

    keywords = service.generate_seo_keywords(content)

    # Verify we get keywords
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert len(keywords) <= 20  # Should not exceed 20 keywords

    # Verify keyword format
    for keyword in keywords:
        assert isinstance(keyword, str)
        assert len(keyword.split()) <= 3  # Each keyword should be max 3 words
        assert keyword.strip() == keyword  # No leading/trailing whitespace
