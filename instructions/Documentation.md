# Markdown Toolset System Design Documentation

## System Architecture Overview
The Markdown toolset is designed with a modular architecture, separating concerns into distinct components for better maintainability and testability.

## Implemented Modules

### 1. Command Line Interface (`cli.py`)
- Handles command-line argument parsing
- Implements the main entry point for the application
- Supports operations:
  - `-a check` for validation
  - `-a post` for publishing
  - `-t wx` for WeChat operations
  - `-t hugo` for Hugo operations

### 2. Markdown File Handler (`md_file.py`)
- Core module for Markdown file processing
- Responsibilities:
  - Parsing Markdown content
  - Front matter management
  - File validation
  - Content transformation

### 3. HTML Generator (`wx_htmler.py`)
- Converts Markdown to HTML format
- Handles special formatting for WeChat platform
- Manages template-based content transformation

### 4. Image Processor (`image_processor.py`)
- Handles image-related operations
- Features:
  - Image availability validation
  - Image reference checking
  - Image path management

### 5. WeChat Publisher (`wx_publisher.py`)
- Manages WeChat platform integration
- Handles article publishing workflow
- Implements WeChat-specific formatting requirements

### 6. Cache Management (`wx_cache.py`)
- Implements caching mechanism
- Manages persistent storage using pickle
- Optimizes performance for repeated operations

### 7. WeChat Client (`wx_client.py`)
- Implements WeChat API integration using WeRobot framework
- Handles authentication and communication with WeChat platform

### 8. OpenRouter Service (`openrouter_service.py`)
- Implements AI-powered content enhancement using OpenRouter API
- Features:
  - Title generation from article content (✅)
    - Generates titles under 100 characters
    - Ensures relevance to content
    - Handles content preprocessing
  - Subtitle/description generation (✅)
    - Generates concise descriptions under 50 characters
    - Ensures proper sentence structure and punctuation
    - Maintains content relevance
  - Tag generation (✅)
    - Generates exactly three tags
    - Smart fallback mechanism
    - Content-based tag extraction
    - Format validation
  - Category suggestion (✅)
    - Predefined categories support
    - New category suggestion
    - Maximum category limit (10)
    - Smart fallback mechanism
  - SEO keyword generation (✅)
    - Generates up to 20 keywords
    - Smart keyword extraction
    - Length control (1-3 words per keyword)
    - Relevance validation
  - Content preprocessing and cleaning
    - Front matter extraction
    - Markdown header cleaning
    - Content truncation for API efficiency
  - Token and length control
    - Configurable temperature and top_p
    - Optimized token limits
    - Smart truncation with ellipsis
  - Integration with OpenAI SDK format
    - Custom system prompts
    - Error handling and validation
  - Comprehensive testing
    - Unit tests with mocked responses
    - Integration tests (skippable)
    - Edge case handling

## Testing Infrastructure
- Comprehensive test suite using pytest
- Test coverage for all major components:
  - CLI functionality tests
  - HTML generation tests
  - Publishing workflow tests
  - Image processing tests
  - Cache management tests
  - Integration tests

## Project Structure
```
wx/
├── cli.py           # Command line interface
├── md_file.py       # Markdown file handling
├── wx_htmler.py     # HTML generation
├── image_processor.py # Image processing
├── wx_publisher.py   # WeChat publishing
├── wx_cache.py      # Cache management
└── wx_client.py     # WeChat API client
└── openrouter_service.py # AI content enhancement
```

## Current Implementation Status
1. ✅ Basic command-line interface
2. ✅ Markdown file processing
3. ✅ HTML generation
4. ✅ Image processing
5. ✅ WeChat publishing framework
6. ✅ Cache management
7. ✅ WeChat API integration
8. ✅ OpenRouter integration
   - ✅ Title generation
   - ✅ Subtitle/description generation
   - ✅ Tag generation
   - ✅ Category suggestion
   - ✅ SEO keyword generation

## Pending Implementation
1. Hugo-specific operations
2. Front matter auto-completion using OpenRouter API
3. Advanced image management
4. Enhanced error handling and reporting