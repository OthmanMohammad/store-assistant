from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    PINECONE_INDEX: str = "store-assistant"
    EMBED_DIM: int = 1024
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/store_assistant"
    
    # Redis (optional for now)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API
    ALLOW_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173,http://127.0.0.1:5173"
    
    # WhatsApp
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_ACCESS_TOKEN: str | None = None
    WHATSAPP_PHONE_ID: str | None = None
    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    MAX_TOKENS: int = 4000
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()