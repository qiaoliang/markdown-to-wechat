import os
from openai import OpenAI
from typing import Optional, List


class OpenRouterService:
    """Service for interacting with OpenRouter API to enhance content."""

    def __init__(self):
        """Initialize the OpenRouter service.

        Raises:
            ValueError: If OPENROUTER_API_KEY environment variable is not set
        """
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is not set")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/your-username/markdown-to-wechat",  # Optional
                "X-Title": "Markdown to WeChat Converter"  # Optional
            }
        )

    def summarize_for_title(self, content: str) -> str:
        """Generate a title from the article content.

        Args:
            content: The full article content including front matter

        Returns:
            A generated title that highlights key points and attracts readers
        """
        # Extract content without front matter
        content_without_front_matter = content.split(
            "---", 1)[1] if "---" in content else content

        # Clean up the content
        content_lines = content_without_front_matter.strip().split("\n")
        # Remove empty lines and clean up markdown headers
        clean_lines = []
        for line in content_lines:
            line = line.strip()
            if not line:
                continue
            # Remove markdown header markers but preserve the text
            if line.startswith('#'):
                line = line.lstrip('#').strip()
            clean_lines.append(line)

        # Take first paragraph (up to 5 lines) for context
        clean_content = " ".join(clean_lines[:5])

        response = self.client.chat.completions.create(
            model="deepseek/deepseek-v3-base:free",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个标题生成器。只生成标题，不要其他文本。标题必须是中文，不超过100个字符，并描述主要主题。不要包含任何markdown、引号或额外的格式。"
                },
                {
                    "role": "user",
                    "content": clean_content
                }
            ],
            temperature=0.3,  # Lower temperature for more focused output
            max_tokens=20,    # Further limit response length
            top_p=0.8,       # More focused token selection
            frequency_penalty=0.0  # No need for frequency penalty in short titles
        )

        title = response.choices[0].message.content.strip()

        # Clean up the title
        title = (title
                 .replace('#', '')
                 .replace('`', '')
                 .replace('"', '')
                 .replace("'", "")
                 .replace("\n", " ")  # Replace newlines with spaces
                 .strip())

        # If title is still too long, truncate it
        if len(title) > 100:
            title = title[:97] + "..."

        # If title is empty, use the first non-empty line from the content
        if not title and clean_lines:
            title = clean_lines[0][:97] + \
                "..." if len(clean_lines[0]) > 100 else clean_lines[0]

        return title

    def summarize_for_subtitle(self, content: str) -> str:
        """Generate a subtitle/description from the article content.

        Args:
            content: The full article content including front matter

        Returns:
            A concise description of the article content in one sentence (max 50 characters)
        """
        # Extract content without front matter
        content_without_front_matter = content.split(
            "---", 1)[1] if "---" in content else content

        # Clean up the content
        content_lines = content_without_front_matter.strip().split("\n")
        # Remove empty lines and clean up markdown headers
        clean_lines = []
        for line in content_lines:
            line = line.strip()
            if not line:
                continue
            # Remove markdown header markers but preserve the text
            if line.startswith('#'):
                line = line.lstrip('#').strip()
            clean_lines.append(line)

        # Take first two paragraphs for context
        clean_content = " ".join(clean_lines[:10])

        response = self.client.chat.completions.create(
            model="deepseek/deepseek-v3-base:free",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个副标题生成器。生成一个单句描述（最多50个字符），捕捉文章的精髓。描述必须是中文，以句号结尾，不应包含任何markdown、引号或额外的格式。"
                },
                {
                    "role": "user",
                    "content": clean_content
                }
            ],
            temperature=0.3,  # Lower temperature for more focused output
            max_tokens=15,    # Limit response length for shorter description
            top_p=0.8,       # More focused token selection
            frequency_penalty=0.0  # No need for frequency penalty in short description
        )

        subtitle = response.choices[0].message.content.strip()

        # Clean up the subtitle
        subtitle = (subtitle
                    .replace('#', '')
                    .replace('`', '')
                    .replace('"', '')
                    .replace("'", "")
                    .replace("\n", " ")  # Replace newlines with spaces
                    .strip())

        # Remove any existing periods or ellipsis
        subtitle = subtitle.rstrip('。.…')

        # Process the subtitle
        if len(subtitle) > 46:
            # For long subtitles, truncate and add ellipsis
            # Remove any trailing punctuation
            subtitle = subtitle[:46].rstrip(',.。!?！？、，')
            return subtitle + "..."
        else:
            # For short subtitles, add period
            return subtitle + "。"

    def generate_tags(self, content: str) -> List[str]:
        """
        Generate exactly three tags for the article content.

        Args:
            content: The article content to analyze

        Returns:
            List of exactly three tags
        """
        prompt = (
            "你是一个标签生成器。根据下面的文章内容，生成恰好三个最能代表文章主题的标签。"
            "每个标签应该：\n"
            "1. 是单个词或带连字符的词\n"
            "2. 只包含字母、数字和连字符\n"
            "3. 与内容相关\n"
            "4. 简洁明了\n\n"
            "内容：\n"
            f"{content}\n\n"
            "只回复三个标签，每行一个，不要标点或解释。标签应该是拼音形式，例如：python-web。"
        )

        response = self._get_response_with_retry(prompt)
        tags = [tag.strip() for tag in response.split('\n') if tag.strip()][:3]

        # Clean up tags
        cleaned_tags = []
        for tag in tags:
            # Remove any non-alphanumeric characters except hyphens
            cleaned = ''.join(c for c in tag if c.isalnum() or c == '-')
            # Remove consecutive hyphens
            while '--' in cleaned:
                cleaned = cleaned.replace('--', '-')
            # Remove leading/trailing hyphens
            cleaned = cleaned.strip('-')
            # Convert to lowercase
            cleaned = cleaned.lower()
            if cleaned:
                cleaned_tags.append(cleaned)

        # If we don't have enough tags, add generic ones
        while len(cleaned_tags) < 3:
            cleaned_tags.append(f"tag-{len(cleaned_tags)+1}")

        return cleaned_tags[:3]  # Ensure we return exactly 3 tags

    def suggest_category(self, content: str, existing_categories: List[str] = None) -> str:
        """
        Suggest a category for the article content.

        Args:
            content: The article content to analyze
            existing_categories: Optional list of existing categories to choose from

        Returns:
            A suggested category name
        """
        # Define predefined categories
        predefined = [
            "个人观点", "实用总结", "方法论",
            "AI编程", "软件工程", "工程效率",
            "人工智能"
        ]

        # If we have maximum categories, only use existing ones
        if existing_categories and len(existing_categories) >= 10:
            return self._get_response_with_retry(
                "你是一个内容分类器。根据下面的文章内容，从以下列表中选择一个最合适的分类：\n"
                f"{', '.join(existing_categories)}\n\n"
                "内容：\n"
                f"{content}\n\n"
                "只回复分类名称，不要解释。"
            )

        # Otherwise, try to use predefined categories first
        category = self._get_response_with_retry(
            "你是一个内容分类器。根据下面的文章内容，从以下列表中选择一个最合适的分类：\n"
            f"{', '.join(predefined)}\n\n"
            "内容：\n"
            f"{content}\n\n"
            "如果没有合适的分类，建议一个新的分类名称（最多3个词）。只回复分类名称，"
            "不要解释或标点。"
        )

        # Clean up the response
        category = category.strip(' .:')  # Remove dots, colons, and spaces
        words = category.split()
        if len(words) > 3:
            # If the category is too long, try to extract key words or use the first three words
            category = ' '.join(words[:3])

        return category

    def generate_seo_keywords(self, content: str) -> List[str]:
        """Generate SEO-friendly keywords from the article content.

        Args:
            content: The full article content including front matter

        Returns:
            A list of up to 20 SEO-friendly keywords
        """
        # Handle empty content
        if not content:
            return []

        # Extract content without front matter
        content_without_front_matter = content.split(
            "---", 1)[1] if "---" in content else content

        # Clean up the content
        content_lines = content_without_front_matter.strip().split("\n")
        clean_lines = []
        for line in content_lines:
            line = line.strip()
            if not line:
                continue
            # Remove markdown header markers but preserve the text
            if line.startswith('#'):
                line = line.lstrip('#').strip()
            clean_lines.append(line)

        # Take first few paragraphs for context
        clean_content = " ".join(clean_lines[:10])

        response = self.client.chat.completions.create(
            model="deepseek/deepseek-v3-base:free",
            messages=[
                {
                    "role": "system",
                    "content": "为给定的文章内容生成SEO关键词。返回最多20个相关的关键词或关键短语。每个关键词/短语应该是1-3个词长。只返回逗号分隔的关键词。关注对搜索引擎优化有价值的中文术语。"
                },
                {
                    "role": "user",
                    "content": clean_content
                }
            ],
            temperature=0.3,  # Lower temperature for more focused output
            max_tokens=100,   # Keywords can be longer than titles/tags
            top_p=0.8        # More focused token selection
        )

        keywords_text = response.choices[0].message.content.strip()

        # Split the comma-separated keywords and clean them
        raw_keywords = [kw.strip() for kw in keywords_text.split(',')]

        # Clean and format each keyword
        keywords = []
        for keyword in raw_keywords:
            # Remove any quotes or special characters
            clean_keyword = (keyword
                             .replace('"', '')
                             .replace("'", "")
                             .replace("[", "")
                             .replace("]", "")
                             .strip())

            # Skip empty keywords
            if not clean_keyword:
                continue

            # Ensure keyword is not too long (max 3 words)
            words = clean_keyword.split()
            if len(words) > 3:
                clean_keyword = " ".join(words[:3])

            # Add keyword if it's unique
            if clean_keyword and clean_keyword not in keywords:
                keywords.append(clean_keyword)

            # Stop if we have 20 keywords
            if len(keywords) >= 20:
                break

        return keywords

    def _get_response_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Get response from OpenRouter API with retry mechanism.

        Args:
            prompt: The prompt to send to the API
            max_retries: Maximum number of retry attempts

        Returns:
            The response text from the API

        Raises:
            RuntimeError: If all retry attempts fail
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="deepseek/deepseek-v3-base:free",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,  # Lower temperature for more focused output
                    max_tokens=50,    # Keep responses concise
                    top_p=0.8        # More focused token selection
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise RuntimeError(
                        f"Failed to get response after {max_retries} attempts: {str(e)}")
                continue  # Try again
