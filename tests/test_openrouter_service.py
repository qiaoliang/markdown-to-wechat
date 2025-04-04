import pytest
from wx.openrouter_service import OpenRouterService


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


def test_init_without_api_key(monkeypatch):
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    with pytest.raises(ValueError) as exc:
        OpenRouterService()
    assert "OPENROUTER_API_KEY environment variable is not set" in str(
        exc.value)


def test_summarize_for_title(mocker, openrouter_service, sample_article_content, mock_openai_response):
    # Mock the OpenAI client's create method
    mock_create = mocker.patch.object(
        openrouter_service.client.chat.completions,
        'create',
        return_value=mock_openai_response
    )

    title = openrouter_service.summarize_for_title(sample_article_content)

    assert title == "Understanding Async IO in Python: A Comprehensive Guide"
    assert mock_create.call_count == 1, "chat.completions.create should be called exactly once"

    # Get and print the actual call arguments for debugging
    call_args = mock_create.call_args
    assert call_args is not None, "Expected create method to be called"

    # Verify the model and messages
    kwargs = call_args.kwargs
    assert kwargs['model'] == "deepseek/deepseek-v3-base:free"
    assert len(kwargs['messages']) == 1

    message_content = kwargs['messages'][0]['content']
    assert "Create a title" in message_content
    assert "highlight key points" in message_content
    assert "attract readers" in message_content
