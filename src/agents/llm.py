import requests
from typing import Optional
import json
import sys
from pathlib import Path
import time

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.tracing import trace_llm_call

class OllamaLLM:
    """Wrapper around local Ollama model for use in LangChain"""
    
    def __init__(
        self,
        model: str = "mistral",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
        top_p: float = 0.9,
    ):
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.top_p = top_p
    
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Generate text using Ollama model.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens in response
        
        Returns:
            Generated text
        """
        with trace_llm_call(prompt, model=self.model) as span:
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "top_p": self.top_p,
                            "num_predict": max_tokens,
                        }
                    },
                    timeout=120  # Agent reasoning can take time
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama error: {response.text}")
                
                result = response.json()['response']
                latency_ms = (time.time() - start_time) * 1000
                
                # Add tracing attributes
                if span:
                    span.set_attribute("response_length", len(result))
                    span.set_attribute("latency_ms", latency_ms)
                    span.set_attribute("max_tokens", max_tokens)
                    span.set_attribute("status_code", response.status_code)
                
                return result
            
            except Exception as e:
                if span:
                    span.set_attribute("error", str(e))
                print(f"LLM error: {e}")
                raise
    
    def __call__(self, prompt: str) -> str:
        """Allow direct call syntax: llm(prompt)"""
        return self.generate(prompt)

def get_llm() -> OllamaLLM:
    """Get singleton LLM instance"""
    return OllamaLLM(model="mistral", temperature=0.3)

if __name__ == "__main__":
    llm = get_llm()
    result = llm("What is data lineage?")
    print(f"✓ LLM working\nResponse: {result[:100]}...")

