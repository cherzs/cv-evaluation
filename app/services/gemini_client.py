"""Gemini LLM Client for CV Evaluation System"""
from typing import Dict, Any
import google.generativeai as genai
from config import Config


class GeminiClient:
    """Google Gemini LLM client implementation"""
    
    def __init__(self):
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            # Use the correct model name for Gemini API
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.temperature = Config.GEMINI_TEMPERATURE
        except ImportError:
            raise ImportError("Google Generative AI not installed. Run: pip install google-generativeai")
        except Exception as e:
            raise Exception(f"Gemini configuration error: {str(e)}")
    
    def chat(self, messages: list) -> str:
        """Call Gemini chat API"""
        try:
            # Convert messages to single prompt
            prompt = self._messages_to_prompt(messages)
            
            # Generate content with proper configuration
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=2048,
                )
            )
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def _messages_to_prompt(self, messages: list) -> str:
        """Convert message list to single prompt string"""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)


# Test function for development
def test_gemini_client():
    """Test function to verify Gemini client works"""
    try:
        client = GeminiClient()
        
        print("Testing Gemini client...")
        
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Say "Hello from Gemini!"'}
        ]
        
        response = client.chat(messages)
        print(f"Response: {response}")
        print("✅ Gemini client working!")
        
    except Exception as e:
        print(f"❌ Error testing Gemini client: {e}")


if __name__ == '__main__':
    test_gemini_client()
