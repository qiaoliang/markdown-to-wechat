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

    def generate_tags(self, content: str) -> List[str]:
        """Generate three relevant tags from the article content.

        Args:
            content: The full article content including front matter

        Returns:
            A list of three tags that best represent the article's topics
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

        # Take first three paragraphs for context
        clean_content = " ".join(clean_lines[:15])

        response = self.client.chat.completions.create(
            model="deepseek/deepseek-v3-base:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are a tag generator. Generate EXACTLY three relevant tags that best represent the article's topics. Return ONLY the tags in a comma-separated format. Each tag should be a single word or short phrase (2-3 words max). The tags should be specific, relevant, and helpful for categorization."
                },
                {
                    "role": "user",
                    "content": clean_content
                }
            ],
            temperature=0.3,  # Lower temperature for more focused output
            max_tokens=20,    # Limit response length
            top_p=0.8,       # More focused token selection
            frequency_penalty=0.0  # No need for frequency penalty in tags
        )

        tags_text = response.choices[0].message.content.strip()

        # Split the comma-separated tags and clean them
        raw_tags = [tag.strip() for tag in tags_text.split(',')]

        # Clean and format each tag
        tags = []
        for tag in raw_tags:
            # Remove any quotes or special characters
            clean_tag = (tag
                         .replace('"', '')
                         .replace("'", "")
                         .replace("[", "")
                         .replace("]", "")
                         .strip())
            # Replace spaces with hyphens and ensure only allowed characters
            clean_tag = "-".join(word.strip() for word in clean_tag.split())
            # Remove any consecutive hyphens
            while "--" in clean_tag:
                clean_tag = clean_tag.replace("--", "-")
            # Remove leading/trailing hyphens
            clean_tag = clean_tag.strip("-")
            if clean_tag:
                tags.append(clean_tag)

        # If we have too many tags, keep only the first 3
        if len(tags) > 3:
            tags = tags[:3]

        # If we don't have enough tags, extract from content
        if len(tags) < 3:
            # First, try to use the first header as a tag
            if clean_lines:
                header_tag = "-".join(word.strip()
                                      for word in clean_lines[0].split())
                if header_tag and header_tag not in tags:
                    tags.append(header_tag)

            # Then, look for key terms in the content
            content_text = " ".join(clean_lines).lower()
            key_terms = ["programming", "development", "software", "python",
                         "javascript", "web", "api", "data", "cloud", "security"]

            # First, try to find exact matches
            for term in key_terms:
                if len(tags) >= 3:
                    break
                if term in content_text and term not in tags:
                    tags.append(term)

            # If we still need more tags, look for partial matches
            if len(tags) < 3:
                for line in clean_lines:
                    if len(tags) >= 3:
                        break
                    words = line.lower().split()
                    for term in key_terms:
                        if len(tags) >= 3:
                            break
                        if any(term in word for word in words) and term not in tags:
                            tags.append(term)

            # If we still need more tags, add generic ones
            while len(tags) < 3:
                generic_tag = f"topic-{len(tags) + 1}"
                if generic_tag not in tags:
                    tags.append(generic_tag)

        return tags

    def suggest_category(self, content: str, existing_categories: List[str] = None) -> str:
        """Generate a category suggestion for the article content.

        Args:
            content: The full article content including front matter
            existing_categories: Optional list of existing categories to check against max limit

        Returns:
            A suggested category that best represents the article's topic
        """
        # Handle empty content
        if not content:
            return "Personal Opinion"

        # Define predefined categories
        PREDEFINED_CATEGORIES = [
            "Personal Opinion", "Practical Summary", "Methodology",
            "AI Programming", "Software Engineering", "Engineering Efficiency",
            "Artificial Intelligence"
        ]

        # If we have max categories (10), only use existing ones
        if existing_categories and len(existing_categories) >= 10:
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

            # Take first paragraph for context
            clean_content = " ".join(clean_lines[:5])

            response = self.client.chat.completions.create(
                model="deepseek/deepseek-v3-base:free",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a category suggester. Given the article content, suggest the most appropriate category from this list: {', '.join(existing_categories)}. Return ONLY the category name, no other text."
                    },
                    {
                        "role": "user",
                        "content": clean_content
                    }
                ],
                temperature=0.3,  # Lower temperature for more focused output
                max_tokens=10,    # Category names are short
                top_p=0.8        # More focused token selection
            )

            suggested_category = response.choices[0].message.content.strip()
            # Ensure we return a valid existing category
            return suggested_category if suggested_category in existing_categories else existing_categories[0]

        # For normal case (less than 10 categories), we can suggest new ones
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

        # Take first paragraph for context
        clean_content = " ".join(clean_lines[:5])

        response = self.client.chat.completions.create(
            model="deepseek/deepseek-v3-base:free",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a category suggester. Given the article content, suggest the most appropriate category. Prefer these predefined categories if they fit: {', '.join(PREDEFINED_CATEGORIES)}. If none fit well, suggest a new concise category (1-3 words). Return ONLY the category name, no other text."
                },
                {
                    "role": "user",
                    "content": clean_content
                }
            ],
            temperature=0.3,  # Lower temperature for more focused output
            max_tokens=10,    # Category names are short
            top_p=0.8        # More focused token selection
        )

        category = response.choices[0].message.content.strip()

        # Clean up the category
        category = (category
                    .replace('"', '')
                    .replace("'", "")
                    .replace("[", "")
                    .replace("]", "")
                    .strip())

        # Ensure we have a valid category
        if not category:
            return "Personal Opinion"

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
                    "content": "Generate SEO keywords for the given article content. Return up to 20 relevant keywords or key phrases. Each keyword/phrase should be 1-3 words long. Return ONLY the keywords in a comma-separated format. Focus on terms that would be valuable for search engine optimization."
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
