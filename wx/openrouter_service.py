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
            api_key=api_key
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

        response = self.client.chat.completions.create(
            model="deepseek/deepseek-v3-base:free",
            messages=[
                {
                    "role": "user",
                    "content": f"""Create a title for the following article that will highlight key points and attract readers. 
                    The title should be concise, informative, and engaging.
                    
                    Article content:
                    {content_without_front_matter}
                    
                    Return only the title, without any additional text or explanation."""
                }
            ]
        )

        return response.choices[0].message.content.strip()
