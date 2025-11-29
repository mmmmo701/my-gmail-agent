from bs4 import BeautifulSoup
import re

class EmailParser:
    """
    A robust utility to clean HTML emails into LLM-friendly plain text.
    """
    
    def __init__(self):
        # Tags we definitely don't want the AI to read
        self.tags_to_remove = [
            'script', 'style', 'meta', 'link', 'head', 'title', 
            'iframe', 'svg', 'path', 'symbol', 'use', 'a'
        ]

    def parse(self, html_content: str) -> str:
        """
        Converts raw HTML into clean, readable text.
        """
        if not html_content:
            return ""

        # 1. Create the Soup
        soup = BeautifulSoup(html_content, 'html.parser')

        # 2. Remove noise (Javascript, CSS, invisible tracking pixels)
        for tag in self.tags_to_remove:
            for element in soup.find_all(tag):
                element.decompose()

        text = soup.get_text(separator='\n', strip=True)

        text = re.sub(r'\n{3,}', '\n', text)
        
        return text.strip()