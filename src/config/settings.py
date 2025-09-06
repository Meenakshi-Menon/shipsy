import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the LangGraph agent project."""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-4o-mini")
    AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.7"))
    AGENT_MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS", "1000"))
    
    # OpenRouter Configuration for DeepSeek
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat-v3.1:free")
    DEEPSEEK_TEMPERATURE = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.3"))
    DEEPSEEK_MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "2000"))
    
    # Brave Search API Configuration
    BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
    BRAVE_SEARCH_COUNT = int(os.getenv("BRAVE_SEARCH_COUNT", "10"))
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required. Please set it in your .env file.")
        if not cls.BRAVE_API_KEY:
            raise ValueError("BRAVE_API_KEY is required. Please set it in your .env file.")
        
        return True
