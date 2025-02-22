import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

class AIEnhancer:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')

    def enhance_metadata(self, title: str, description: str) -> dict:
        """Enhance title and description using Gemini AI."""
        try:
            prompt = (
                f"Original Title: {title}\n"
                f"Original Description: {description}\n\n"
                "Create a concise and engaging title (max 60 chars) and "
                "brief description (max 150 chars). "
                "Format:\nTitle: [enhanced]\nDescription: [enhanced]"
            )

            response = self.model.generate_content(prompt)
            
            # Parse the response
            lines = response.text.split('\n')
            enhanced_title = lines[0].replace('Title: ', '').strip()
            enhanced_description = lines[1].replace('Description: ', '').strip()

            return {
                'title': enhanced_title,
                'description': enhanced_description,
                'original': {
                    'title': title,
                    'description': description
                }
            }

        except Exception as e:
            logger.error(f"AI enhancement error: {e}")
            return {
                'title': title,
                'description': description
            }