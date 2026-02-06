"""
AI Engine - Claude API wrapper for ORACLE
Handles all AI operations (classification, generation, analysis)
"""
import anthropic
from typing import Optional
from core.config import settings

class AIEngine:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def classify_text(self, text: str, categories: list) -> dict:
        """
        Classify text into categories using Haiku (fast & cheap)
        """
        prompt = f"""Classify the following text into ONE of these categories: {', '.join(categories)}

Text: {text}

Return only: {"category": "CATEGORY_NAME", "confidence": 0.0-1.0, "reason": "brief reason"}"""
        
        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL_HAIKU,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "result": response.content[0].text,
            "model": "haiku",
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens
        }
    
    async def analyze_content(self, content: str, task: str) -> dict:
        """
        Deep analysis using Sonnet (balanced)
        """
        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL_SONNET,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"{task}\n\nContent:\n{content}"
            }]
        )
        
        return {
            "result": response.content[0].text,
            "model": "sonnet",
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens
        }
    
    async def generate_content(self, prompt: str, format: str = "text") -> dict:
        """
        Generate content (tweets, threads, emails) using Sonnet
        """
        system_prompt = f"You are a crypto/AI expert content creator. Format your response as {format}."
        
        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL_SONNET,
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "content": response.content[0].text,
            "model": "sonnet",
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens
        }
    
    async def complex_task(self, prompt: str) -> dict:
        """
        Complex reasoning using Opus (premium)
        Used for: strategic decisions, complex analysis, edge cases
        """
        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL_OPUS,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "result": response.content[0].text,
            "model": "opus",
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens
        }

# Global instance
ai_engine = AIEngine()
