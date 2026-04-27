"""
AI Service with Gemini and Groq fallback functionality.
Provides a unified interface for AI operations with automatic fallback.
"""

import logging
import requests
import json
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

class AIService:
    """Unified AI service with Gemini and Groq fallback"""
    
    def __init__(self):
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
        self.gemini_available = self._check_gemini_availability()
        self.groq_available = self._check_groq_availability()
        
    def _check_gemini_availability(self) -> bool:
        """Check if Gemini API is available and working"""
        try:
            if not self.gemini_api_key or self.gemini_api_key in ['NOT_FOUND', 'GEMINI_API_KEY']:
                return False
            
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Test with a simple request
            response = model.generate_content("Test")
            return response and response.text is not None
        except Exception as e:
            logger.warning(f"Gemini API not available: {e}")
            return False
    
    def _check_groq_availability(self) -> bool:
        """Check if Groq API is available and working"""
        try:
            if not self.groq_api_key or self.groq_api_key in ['NOT_FOUND', 'GROQ_API_KEY']:
                return False
            
            headers = {
                'Authorization': f'Bearer {self.groq_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messages': [{'role': 'user', 'content': 'Test'}],
                'model': 'llama-3.3-70b-versatile',
                'max_tokens': 10
            }
            
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Groq API not available: {e}")
            return False
    
    def generate_content(self, prompt: str, system_prompt: str = None, max_tokens: int = 500) -> str:
        """Generate content using available AI service with fallback"""
        
        # Try Gemini first if available
        if self.gemini_available:
            try:
                return self._generate_with_gemini(prompt, system_prompt)
            except Exception as e:
                logger.warning(f"Gemini failed, trying Groq: {e}")
                self.gemini_available = False  # Mark as unavailable for this session
        
        # Fallback to Groq
        if self.groq_available:
            try:
                return self._generate_with_groq(prompt, system_prompt, max_tokens)
            except Exception as e:
                logger.warning(f"Groq failed: {e}")
                self.groq_available = False  # Mark as unavailable for this session
        
        # If both fail, return fallback response
        return self._get_fallback_response(prompt)
    
    def _generate_with_gemini(self, prompt: str, system_prompt: str = None) -> str:
        """Generate content using Gemini API"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {prompt}"
            
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                raise Exception("Empty response from Gemini")
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise e
    
    def _generate_with_groq(self, prompt: str, system_prompt: str = None, max_tokens: int = 500) -> str:
        """Generate content using Groq API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.groq_api_key}',
                'Content-Type': 'application/json'
            }
            
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            
            payload = {
                'messages': messages,
                'model': 'llama-3.3-70b-versatile',
                'temperature': 0.7,
                'max_tokens': max_tokens,
                'top_p': 0.9
            }
            
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                raise Exception(f"Groq API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise e
    
    def _get_fallback_response(self, prompt: str) -> str:
        """Provide intelligent fallback responses when all APIs fail"""
        prompt_lower = prompt.lower()
        
        # Startup/entrepreneurship related responses
        if any(word in prompt_lower for word in ['startup', 'funding', 'investment', 'business']):
            return """I understand you're asking about startup and business topics. While I'm experiencing some technical difficulties with my AI services, I can provide some general guidance:

• Focus on solving a real problem that people are willing to pay for
• Validate your idea with potential customers before building
• Create a clear business model and revenue projections
• Build a strong team with complementary skills
• Consider the market size and competition

For more detailed advice, please try again in a few moments when our AI services are fully operational."""
        
        # Technical questions
        elif any(word in prompt_lower for word in ['technical', 'code', 'development', 'programming']):
            return """I'd be happy to help with technical questions! Currently experiencing some connectivity issues with our AI services, but here are some general technical principles:

• Write clean, maintainable code with proper documentation
• Follow best practices and design patterns
• Implement proper error handling and logging
• Use version control and automated testing
• Consider scalability and performance from the start

Please try your question again in a moment for more specific technical guidance."""
        
        # General questions
        else:
            return """I'm currently experiencing some technical difficulties with our AI services, but I'm here to help! 

Please try rephrasing your question or ask again in a few moments. Our team is working to restore full AI functionality.

In the meantime, feel free to explore our platform's other features like browsing projects, connecting with entrepreneurs, or checking out our funding resources."""
    
    def is_available(self) -> bool:
        """Check if any AI service is available"""
        return self.gemini_available or self.groq_available
    
    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all AI services"""
        return {
            'gemini_available': self.gemini_available,
            'groq_available': self.groq_available,
            'any_available': self.is_available()
        }

# Global AI service instance
ai_service = AIService()
