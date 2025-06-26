from pydantic_settings import BaseSettings , SettingsConfigDict
from typing import Optional

class Config(BaseSettings):
    OPENAI_API_KEY: Optional[str] = None
    COMET_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env")

config = Config()
