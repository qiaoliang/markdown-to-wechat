"""Test cases for the error handling system"""

import pytest
import logging
import time
from datetime import datetime
from wx.error_handler import (
    ErrorHandler,
    ErrorLevel,
    ErrorCategory,
    ErrorContext,
    MarkdownToolError,
    ValidationError,
    APIError,
    FileSystemError,
    ImageError,
    CacheError,
    HugoError,
    RetryStrategy,
)


@pytest.fixture
def error_handler():
    """Create a test error handler instance"""
    handler = ErrorHandler()
    return handler


@pytest.fixture
def mock_logger(mocker):
    """Create a mock logger"""
    return mocker.Mock(spec=logging.Logger)


def test_error_handler_initialization(error_handler):
    """Test error handler initialization"""
    assert error_handler._recovery_strategies == {}
    assert error_handler._error_count == {cat: 0 for cat in ErrorCategory}
    assert error_handler._max_retries == 3


def test_handle_markdown_tool_error(error_handler, mock_logger, caplog):
    """Test handling of MarkdownToolError"""
    error_handler.logger = mock_logger
    error = ValidationError("Invalid markdown format")

    error_handler.handle_error(error)

    # Verify error was logged
    mock_logger.error.assert_called_once()
    assert "Invalid markdown format" in mock_logger.error.call_args[0][0]

    # Verify error count was updated
    assert error_handler.get_error_count(ErrorCategory.VALIDATION) == 1


def test_handle_standard_exception(error_handler, mock_logger):
    """Test handling of standard Python exception"""
    error_handler.logger = mock_logger
    error = ValueError("Standard error")

    error_handler.handle_error(error)

    # Verify error was logged
    mock_logger.error.assert_called_once()
    assert "Standard error" in mock_logger.error.call_args[0][0]

    # Verify error count was updated
    assert error_handler.get_error_count(ErrorCategory.SYSTEM) == 1


def test_recovery_strategy_registration(error_handler):
    """Test registration and execution of recovery strategies"""
    recovery_executed = False

    def test_strategy(context):
        nonlocal recovery_executed
        recovery_executed = True

    error_handler.register_recovery_strategy(
        ErrorCategory.IMAGE, test_strategy)
    error = ImageError("Image not found")

    error_handler.handle_error(error)

    assert recovery_executed
    assert ErrorCategory.IMAGE in error_handler._recovery_strategies


def test_error_count_management(error_handler):
    """Test error count tracking and reset"""
    # Generate some errors
    error_handler.handle_error(ValidationError("Error 1"))
    error_handler.handle_error(ValidationError("Error 2"))
    error_handler.handle_error(APIError("Error 3"))

    # Check counts
    assert error_handler.get_error_count(ErrorCategory.VALIDATION) == 2
    assert error_handler.get_error_count(ErrorCategory.API) == 1

    # Reset specific category
    error_handler.reset_error_count(ErrorCategory.VALIDATION)
    assert error_handler.get_error_count(ErrorCategory.VALIDATION) == 0
    assert error_handler.get_error_count(ErrorCategory.API) == 1

    # Reset all
    error_handler.reset_error_count()
    assert sum(error_handler.get_error_count().values()) == 0


def test_retry_decorator(error_handler):
    """Test retry decorator with different strategies"""
    attempts = 0

    @error_handler.retry(max_retries=3, strategy=RetryStrategy.LINEAR_BACKOFF)
    def failing_function():
        nonlocal attempts
        attempts += 1
        raise ValueError("Temporary error")

    start_time = time.time()
    with pytest.raises(ValueError):
        failing_function()
    duration = time.time() - start_time

    assert attempts == 3  # Original attempt + 2 retries
    assert duration >= 3  # Should take at least 3 seconds with linear backoff


def test_user_message_formatting(error_handler, capsys):
    """Test user-friendly error message formatting"""
    # Test different error levels
    error_handler.handle_error(ValidationError(
        "Validation issue", ErrorLevel.WARNING))
    captured = capsys.readouterr()
    assert "⚠️ Warning" in captured.out

    error_handler.handle_error(APIError("API failure", ErrorLevel.CRITICAL))
    captured = capsys.readouterr()
    assert "🚨 Critical Error" in captured.out

    # Test category-specific help messages
    error_handler.handle_error(FileSystemError("File not found"))
    captured = capsys.readouterr()
    assert "Please check file permissions and paths" in captured.out


def test_error_context_creation():
    """Test error context creation and attributes"""
    error = ValidationError("Test error")
    context = error.context

    assert context.message == "Test error"
    assert context.category == ErrorCategory.VALIDATION
    assert context.level == ErrorLevel.ERROR
    assert isinstance(context.timestamp, datetime)
    assert context.source_file.endswith("test_error_handler.py")
    assert context.stack_trace is not None


def test_multiple_recovery_strategies(error_handler):
    """Test multiple recovery strategies for the same category"""
    strategy1_executed = False
    strategy2_executed = False

    def strategy1(context):
        nonlocal strategy1_executed
        strategy1_executed = True
        raise Exception("Strategy 1 failed")

    def strategy2(context):
        nonlocal strategy2_executed
        strategy2_executed = True

    error_handler.register_recovery_strategy(ErrorCategory.CACHE, strategy1)
    error_handler.register_recovery_strategy(ErrorCategory.CACHE, strategy2)

    error_handler.handle_error(CacheError("Cache error"))

    assert strategy1_executed
    assert strategy2_executed  # Second strategy should execute after first fails


def test_error_handler_thread_safety(error_handler):
    """Test error handler in multi-threaded environment"""
    import threading

    def generate_errors():
        for _ in range(100):
            error_handler.handle_error(ValidationError("Thread error"))

    threads = [threading.Thread(target=generate_errors) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert error_handler.get_error_count(ErrorCategory.VALIDATION) == 500
