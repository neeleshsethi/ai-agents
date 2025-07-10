from pydantic_settings import BaseSettings , SettingsConfigDict
from typing import Optional
import os

class Config(BaseSettings):
    OPENAI_API_KEY: Optional[str] = None
    COMET_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_MODEL_PROVIDER: str = "openai"
    GENERATION_MODEL_PROVIDER: Optional[str] = None
    GENERATION_MODEL: str = "gpt-4o-mini"
    COMET_ENDPOINT: str = "https://www.comet.com/api/v1"
    COMET_PROJECT: str = "ai-agents"
    COMET_TRACING: bool = False
    QDRANT_URL: str = "https://c006961b-c63f-469e-b947-33bbfe692e0c.us-east-1-0.aws.cloud.qdrant.io:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "electronics"
    




    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

print(f"Environment variable QDRANT_COLLECTION_NAME: {os.getenv('QDRANT_COLLECTION_NAME')}")

try:
    config = Config()
    print(f"Config loaded successfully. Collection name: {config.QDRANT_COLLECTION_NAME}")
except Exception as e:
    print(f"Error loading config: {e}")
    # Create config with defaults if .env fails to load
    config = Config(_env_file=None)
    print(f"Config loaded with defaults. Collection name: {config.QDRANT_COLLECTION_NAME}")
