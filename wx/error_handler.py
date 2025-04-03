"""
Error handling system for the Markdown toolset.
Provides centralized error management, logging, and user feedback.
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Callable, TypeVar, Union
from dataclasses import dataclass
from datetime import datetime
import logging
import os
import traceback
from functools import wraps
import inspect
import sys


class ErrorLevel(Enum):
    """Error severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Categories for different types of errors"""
    VALIDATION = "VALIDATION"  # Format/content validation errors
    API = "API"  # API-related errors (OpenRouter/WeChat)
    FILE_SYSTEM = "FILE_SYSTEM"  # File operation errors
    IMAGE = "IMAGE"  # Image processing errors
    CACHE = "CACHE"  # Cache operation errors
    MARKDOWN = "MARKDOWN"  # Markdown processing errors
    HUGO = "HUGO"  # Hugo-specific errors
    SYSTEM = "SYSTEM"  # System-level errors
    GENERAL = "GENERAL"  # General errors


@dataclass
class ErrorContext:
    """Context information for errors"""
    message: str
    category: ErrorCategory
    level: ErrorLevel
    timestamp: datetime
    source_file: str
    line_number: int
    function_name: str
    stack_trace: str
    additional_info: Optional[Dict[str, Any]] = None


class MarkdownToolError(Exception):
    """Base exception class for all Markdown tool errors"""

    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.GENERAL, level: ErrorLevel = ErrorLevel.ERROR):
        super().__init__(message)

        # Get the caller's frame by walking up the stack
        frame = inspect.currentframe()
        try:
            while frame:
                module_name = frame.f_globals.get('__name__', '')
                if not module_name.startswith('wx.') and not module_name.startswith('pytest'):
                    break
                frame = frame.f_back

            if frame:
                filename = frame.f_code.co_filename
                lineno = frame.f_lineno
                function = frame.f_code.co_name
            else:
                filename = "<unknown>"
                lineno = 0
                function = "<unknown>"

            # Always capture a stack trace
            stack_trace = ''.join(traceback.format_stack())

            self.context = ErrorContext(
                message=message,
                category=category,
                level=level,
                timestamp=datetime.now(),
                source_file=filename,
                line_number=lineno,
                function_name=function,
                stack_trace=stack_trace
            )
        finally:
            del frame  # Avoid reference cycles


class ValidationError(MarkdownToolError):
    """Raised when validation fails for Markdown content or configuration"""

    def __init__(self, message: str, level: ErrorLevel = ErrorLevel.ERROR):
        super().__init__(message, ErrorCategory.VALIDATION, level)


class APIError(MarkdownToolError):
    """Raised when API operations fail (OpenRouter/WeChat)"""

    def __init__(self, message: str, level: ErrorLevel = ErrorLevel.ERROR):
        super().__init__(message, ErrorCategory.API, level)


class FileSystemError(MarkdownToolError):
    """Raised when file operations fail"""

    def __init__(self, message: str, level: ErrorLevel = ErrorLevel.ERROR):
        super().__init__(message, ErrorCategory.FILE_SYSTEM, level)


class ImageError(MarkdownToolError):
    """Raised when image processing operations fail"""

    def __init__(self, message: str, level: ErrorLevel = ErrorLevel.ERROR):
        super().__init__(message, ErrorCategory.IMAGE, level)


class CacheError(MarkdownToolError):
    """Raised when cache operations fail"""

    def __init__(self, message: str, level: ErrorLevel = ErrorLevel.ERROR):
        super().__init__(message, ErrorCategory.CACHE, level)


class HugoError(MarkdownToolError):
    """Raised when Hugo-specific operations fail"""

    def __init__(self, message: str, level: ErrorLevel = ErrorLevel.ERROR):
        super().__init__(message, ErrorCategory.HUGO, level)


class RetryStrategy(Enum):
    """Retry strategies for error recovery"""
    NO_RETRY = "NO_RETRY"
    IMMEDIATE = "IMMEDIATE"
    LINEAR_BACKOFF = "LINEAR_BACKOFF"
    EXPONENTIAL_BACKOFF = "EXPONENTIAL_BACKOFF"


class ErrorHandler:
    """Centralized error handler for the Markdown toolset"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the error handler"""
        self.logger = logger or logging.getLogger(__name__)
        self._recovery_strategies: Dict[ErrorCategory, List[Callable]] = {}
        self._error_count: Dict[ErrorCategory, int] = {
            cat: 0 for cat in ErrorCategory}
        self._max_retries = 3

    def handle_error(self, error: Union[MarkdownToolError, Exception], context: Optional[Dict[str, Any]] = None) -> None:
        """Handle an error with appropriate logging and recovery strategies"""
        if isinstance(error, MarkdownToolError):
            error_context = error.context
        else:
            # Convert standard exception to MarkdownToolError
            error_context = ErrorContext(
                message=str(error),
                category=ErrorCategory.SYSTEM,
                level=ErrorLevel.ERROR,
                timestamp=datetime.now(),
                source_file=traceback.extract_stack()[-2].filename,
                line_number=traceback.extract_stack()[-2].lineno,
                function_name=traceback.extract_stack()[-2].name,
                stack_trace=traceback.format_exc(),
                additional_info=context
            )

        # Log the error
        self._log_error(error_context)

        # Update error count
        self._error_count[error_context.category] += 1

        # Try to recover
        self._attempt_recovery(error_context)

        # Format user message
        user_message = self._format_user_message(error_context)
        print(user_message)

    def _log_error(self, context: ErrorContext) -> None:
        """Log error with appropriate level and context"""
        log_message = (
            f"[{context.category.value}] {context.message}\n"
            f"Location: {context.source_file}:{context.line_number} in {context.function_name}\n"
            f"Additional Info: {context.additional_info if context.additional_info else 'None'}"
        )

        if context.level == ErrorLevel.CRITICAL:
            self.logger.critical(log_message)
        elif context.level == ErrorLevel.ERROR:
            self.logger.error(log_message)
        elif context.level == ErrorLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def _attempt_recovery(self, context: ErrorContext) -> None:
        """Attempt to recover from an error using registered recovery strategies"""
        if context.category in self._recovery_strategies:
            for strategy in self._recovery_strategies[context.category]:
                try:
                    strategy(context)
                    self.logger.info(
                        f"Successfully recovered from {context.category.value} error")
                    return
                except Exception as e:
                    self.logger.warning(f"Recovery strategy failed: {str(e)}")

    def _format_user_message(self, context: ErrorContext) -> str:
        """Format error message for user display"""
        if context.level == ErrorLevel.CRITICAL:
            prefix = "🚨 Critical Error"
        elif context.level == ErrorLevel.ERROR:
            prefix = "❌ Error"
        elif context.level == ErrorLevel.WARNING:
            prefix = "⚠️ Warning"
        else:
            prefix = "ℹ️ Info"

        message = f"{prefix}: {context.message}"

        # Add helpful suggestions based on error category
        if context.category == ErrorCategory.FILE_SYSTEM:
            message += "\nPlease check file permissions and paths."
        elif context.category == ErrorCategory.API:
            message += "\nPlease verify your API credentials and network connection."
        elif context.category == ErrorCategory.IMAGE:
            message += "\nPlease verify image files and formats."

        return message

    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable) -> None:
        """Register a recovery strategy for a specific error category"""
        if category not in self._recovery_strategies:
            self._recovery_strategies[category] = []
        self._recovery_strategies[category].append(strategy)

    def get_error_count(self, category: Optional[ErrorCategory] = None) -> Union[int, Dict[ErrorCategory, int]]:
        """Get error count for a specific category or all categories"""
        if category:
            return self._error_count[category]
        return self._error_count.copy()

    def reset_error_count(self, category: Optional[ErrorCategory] = None) -> None:
        """Reset error count for a specific category or all categories"""
        if category:
            self._error_count[category] = 0
        else:
            self._error_count = {cat: 0 for cat in ErrorCategory}

    @staticmethod
    def retry(max_retries: int = 3, strategy: RetryStrategy = RetryStrategy.LINEAR_BACKOFF):
        """Decorator for automatic retry on failure"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries - 1:
                            # Calculate delay based on strategy
                            if strategy == RetryStrategy.IMMEDIATE:
                                delay = 0
                            elif strategy == RetryStrategy.LINEAR_BACKOFF:
                                delay = attempt + 1
                            elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                                delay = 2 ** attempt
                            else:
                                raise last_exception

                            if delay > 0:
                                import time
                                time.sleep(delay)
                            continue
                raise last_exception
            return wrapper
        return decorator


# Global error handler instance
error_handler = ErrorHandler()

# Example recovery strategy registration


def _image_recovery_strategy(context: ErrorContext) -> None:
    """Example recovery strategy for image errors"""
    if "unavailable" in context.message.lower():
        # Try to use default image
        logging.info("Attempting to use default image as recovery strategy")
        # Implementation would go here
        pass


error_handler.register_recovery_strategy(
    ErrorCategory.IMAGE, _image_recovery_strategy)

# Configure logging


def setup_logging(log_dir: str = "logs") -> None:
    """Setup logging configuration"""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(
        log_dir, f"markdown_tool_{datetime.now().strftime('%Y%m%d')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
