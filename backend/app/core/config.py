from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置，从环境变量或 .env 文件读取"""

    
    DATABASE_URL: str = "sqlite+aiosqlite:///./translation.db"

    #
    OPENAI_API_KEY: str = Field(...)  
    OPENAI_API_BASE: str = "https://api.deepseek.com/v1"  
    OPENAI_API_VERSION: str = "deepseek-chat"  

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
