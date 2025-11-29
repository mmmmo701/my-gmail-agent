import ollama
import os
from dotenv import load_dotenv
from src.prompts import ANALYSIS_SYSTEM_PROMPT

# Load environment variables
load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

class OllamaClient:
    def analyze_email(self, email_body):
        """
        Sends email text to Ollama and returns a dictionary with summary and category.
        """
        # Truncate body to avoid context limit errors (approx 4000 chars is safe/fast)
        clean_body = email_body[:4000]
        
        prompt = f"Email Content:\n{clean_body}"

        try:
            response = ollama.chat(model=MODEL, messages=[
                {'role': 'system', 'content': ANALYSIS_SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt},
            ])
            
            content = response['message']['content']
            return self._parse_response(content)

        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return {"summary": "Error analyzing email", "category": "Unknown"}

    def _parse_response(self, text):
        """
        Parses the strict output format from the LLM into a dictionary.
        Expected format:
        Summary: ...
        Category: ...
        """
        lines = text.strip().split('\n')
        result = {"summary": "Could not parse summary", "category": "Unknown"}
        
        for line in lines:
            if line.lower().startswith("summary:"):
                result["summary"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("category:"):
                result["category"] = line.split(":", 1)[1].strip()
        
        return result