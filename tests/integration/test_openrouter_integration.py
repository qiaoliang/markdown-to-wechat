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
