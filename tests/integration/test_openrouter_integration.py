import pytest
import os
from wx.openrouter_service import OpenRouterService


def check_openrouter_key():
    """Skip test if OPENROUTER_API_KEY is not set."""
    return pytest.mark.skipif(
        not os.getenv('OPENROUTER_API_KEY'),
        reason="OPENROUTER_API_KEY environment variable is not set"
    )


@pytest.mark.skip(reason="Integration test that calls OpenRouter API. Run manually when needed.")
def test_openrouter_title_generation():
    """Integration test for title generation using real OpenRouter API.

    This test is skipped by default to avoid unnecessary API calls.
    To run this test, use: pytest tests/integration/test_openrouter_integration.py -v --no-skip
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

    # The title should contain relevant keywords
    relevant_terms = ['python', 'async', 'io', 'asynchronous']
    assert any(term.lower() in title.lower() for term in relevant_terms), \
        f"Title '{title}' should contain at least one of these terms: {relevant_terms}"


@pytest.mark.skip(reason="Integration test that calls OpenRouter API. Run manually when needed.")
def test_openrouter_subtitle_generation():
    """Integration test for subtitle generation using real OpenRouter API.

    This test is skipped by default to avoid unnecessary API calls.
    To run this test, use: pytest tests/integration/test_openrouter_integration.py -v -s
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

    # The subtitle should contain relevant keywords
    relevant_terms = ['python', 'async', 'io', 'asynchronous']
    assert any(term.lower() in subtitle.lower() for term in relevant_terms), \
        f"Subtitle '{subtitle}' should contain at least one of these terms: {relevant_terms}"

    # The subtitle should be a complete sentence
    assert subtitle[-1] in '.!?', \
        f"Subtitle '{subtitle}' should end with proper punctuation"


@pytest.mark.skip(reason="Integration test that calls OpenRouter API - run manually")
def test_openrouter_tag_generation():
    """Integration test for tag generation using real OpenRouter API."""
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

    # The tags should contain relevant keywords
    relevant_terms = ['python', 'async', 'io', 'asynchronous', 'coroutine']
    found_relevant = False
    for tag in tags:
        if any(term.lower() in tag.lower() for term in relevant_terms):
            found_relevant = True
            break
    assert found_relevant, \
        f"Tags {tags} should contain at least one of these terms: {relevant_terms}"

    # Tags should be unique
    assert len(set(tags)) == 3, "All tags should be unique"

    # Print tags for manual inspection
    print(f"\nGenerated tags: {tags}")


@pytest.mark.skip(reason="Integration test that calls OpenRouter API - run manually")
def test_openrouter_category_suggestion():
    """Integration test for category suggestion using real OpenRouter API."""
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
    predefined = ["Personal Opinion", "Practical Summary", "Methodology",
                  "AI Programming", "Software Engineering", "Engineering Efficiency",
                  "Artificial Intelligence"]
    if category not in predefined:
        # If not predefined, should be reasonable length and format
        assert len(category.split()
                   ) <= 3, f"Category '{category}' should be at most 3 words"
        assert all(c.isalnum() or c.isspace() for c in category), \
            f"Category '{category}' should only contain letters, numbers, and spaces"

    # Test with maximum categories (should only use existing ones)
    existing_categories = predefined + \
        ["Web Development", "Mobile Development", "Data Science"]
    category_max = service.suggest_category(content, existing_categories)
    assert category_max in existing_categories, \
        f"Category '{category_max}' should be one of existing categories when at max limit"

    # Print categories for manual inspection
    print(f"\nGenerated category (no existing): {category}")
    print(f"Generated category (max limit): {category_max}")
