import os
from openai import OpenAI
from typing import Optional


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
                    "content": "You are a title generator. Generate ONLY a title, no other text. The title must be in English, under 100 characters, and describe the main topic. Do not include any markdown, quotes, or additional formatting."
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
                    "content": "You are a subtitle generator. Generate ONLY a single sentence description (max 50 characters) that captures the essence of the article. The description must be in English, end with a period, and should not include any markdown, quotes, or additional formatting."
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

        # Ensure subtitle ends with proper punctuation
        if subtitle and subtitle[-1] not in '.!?':
            subtitle = subtitle + '.'

        # If subtitle is too long after adding punctuation, truncate it and add ellipsis
        if len(subtitle) > 50:
            subtitle = subtitle[:46] + "..."

        # If subtitle is empty, use the first non-empty line from the content
        if not subtitle and clean_lines:
            first_line = clean_lines[0]
            if len(first_line) > 46:
                subtitle = first_line[:46] + "..."
            else:
                subtitle = first_line + "."

        return subtitle
