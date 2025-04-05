# Markdown Toolset System Design Documentation

## System Architecture Overview
The Markdown toolset is designed with a modular architecture, separating concerns into distinct components for better maintainability and testability.

## Core Components

### 1. Command Line Interface (`cli.py`)
- Handles command-line argument parsing
- Implements the main entry point for the application
- Supports operations:
  - `-a check` for validation
  - `-a post` for publishing
  - `-t wx` for WeChat operations
  - `-t hugo` for Hugo operations
- Current coverage: 16%

### 2. Markdown File Handler (`md_file.py`)
- Core module for Markdown file processing
- Responsibilities:
  - Parsing Markdown content
  - Front matter management
  - File validation
  - Content transformation
- Current coverage: 80%

### 3. HTML Generator (`wx_htmler.py`)
- Converts Markdown to HTML format
- Handles special formatting for WeChat platform
- Manages template-based content transformation
- Current coverage: 96%

### 4. Image Processing System
#### 4.1 Image Processor (`image_processor.py`)
- Handles image-related operations
- Features:
  - Image availability validation
  - Image reference checking
  - Image path management
- Current coverage: 95%

#### 4.2 Image Reference Handler (`image_reference.py`)
- Detects and processes image references
- Supports both Markdown and HTML formats
- Handles relative and absolute paths
- Current coverage: 95%

#### 4.3 Image Error Handler (`image_errors.py`)
- Custom error classes for image processing
- Validation functions for images
- Network image handling
- Current coverage: 99%

### 5. Hugo Processing System
#### 5.1 Hugo Processor (`hugo_processor.py`)
- Manages Hugo-specific operations
- Features:
  - File copying and structure maintenance
  - Environment variable handling
  - Image reference updating
  - Directory structure management
- Current coverage: 77%

#### 5.2 Empty Line Processor (`empty_line_processor.py`)
- Handles empty line management
- Preserves semantic structure
- Special case handling for code blocks and lists
- Current coverage: 97%

#### 5.3 Front Matter Handler (`hugo_front_matter.py`)
- Manages Hugo front matter
- Format standardization
- Validation and parsing
- Current coverage: 95%

### 6. WeChat Integration
#### 6.1 WeChat Publisher (`wx_publisher.py`)
- Manages WeChat platform integration
- Handles article publishing workflow
- Implements WeChat-specific formatting
- Current coverage: 79%

#### 6.2 WeChat Client (`wx_client.py`)
- Implements WeChat API integration
- Handles authentication and communication
- Current coverage: 26%

### 7. Cache Management (`wx_cache.py`)
- Implements caching mechanism
- Manages persistent storage
- Optimizes performance
- Current coverage: 73%

### 8. Error Handling (`error_handler.py`)
- Centralized error management
- Custom exception hierarchy
- Recovery strategies
- Error tracking and reporting
- Current coverage: 88%

### 9. OpenRouter Integration (`openrouter_service.py`)
- AI-powered content enhancement
- Features:
  - Title generation
  - Description generation
  - Tag generation
  - Category suggestion
  - SEO keyword generation
- Current coverage: 79%

## Project Structure
```
wx/
├── __init__.py
├── cli.py                  # Command line interface
├── md_file.py             # Markdown file handling
├── wx_htmler.py           # HTML generation
├── image_processor.py      # Image processing
├── image_reference.py     # Image reference handling
├── image_errors.py        # Image error handling
├── hugo_processor.py      # Hugo operations
├── empty_line_processor.py # Empty line management
├── hugo_front_matter.py   # Front matter handling
├── wx_publisher.py        # WeChat publishing
├── wx_cache.py           # Cache management
├── wx_client.py          # WeChat API client
├── error_handler.py      # Error handling system
└── openrouter_service.py # AI content enhancement
```

## Testing Infrastructure
- Framework: pytest
- Coverage tracking: pytest-cov
- Mock support: pytest-mock
- Current test status:
  - Total tests: 133
  - Passed: 126
  - Skipped: 7 (Integration tests)
  - Overall coverage: 77%

## API Documentation
### Hugo Operations
1. Empty Line Processing
   - Input: Markdown content
   - Output: Processed content with standardized empty lines
   - Rules: See Empty Line Removal section

2. Front Matter Processing
   - Input: Markdown front matter
   - Output: Standardized front matter
   - Format: `key="value"` or `key: value`

3. Image Reference Processing
   - Input: Markdown content with image references
   - Output: Updated content with processed image references
   - Supported formats: Markdown and HTML image tags

### WeChat Operations
1. Image Validation
   - Input: Markdown file path
   - Output: Validation results
   - Checks: Image availability and accessibility

2. Article Publishing
   - Input: Markdown content
   - Output: Publishing status
   - Process: Format conversion and WeChat API integration

### OpenRouter Integration
1. Content Enhancement
   - Input: Article content
   - Output: Enhanced metadata
   - Features: Title, description, tags, categories, keywords generation

## Error Handling
- Centralized error management through `ErrorHandler`
- Custom exceptions for specific scenarios
- Recovery strategies for common issues
- Comprehensive error reporting

## Cache Management
- File-based caching using pickle
- Cache invalidation strategies
- Performance optimization

## Integration Guidelines
1. WeChat Integration
   - API authentication
   - Content formatting
   - Error handling

2. Hugo Integration
   - Environment setup
   - Directory structure
   - File management

3. OpenRouter Integration
   - API key management
   - Request formatting
   - Response handling