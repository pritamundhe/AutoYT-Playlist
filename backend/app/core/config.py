"""
Configuration management using Pydantic Settings
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "YouTube Playlist Generator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 86400  # 24 hours
    
    # YouTube API
    YOUTUBE_API_KEY: str
    YOUTUBE_API_QUOTA_LIMIT: int = 10000
    YOUTUBE_CACHE_TTL: int = 86400
    
    # NLP Models
    SENTENCE_TRANSFORMER_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_sm"
    
    # Ranking Weights
    WEIGHT_VIEWS: float = 0.15
    WEIGHT_LIKES: float = 0.20
    WEIGHT_SUBSCRIBERS: float = 0.10
    WEIGHT_RELEVANCE: float = 0.40
    WEIGHT_RECENCY: float = 0.10
    WEIGHT_DURATION_PENALTY: float = 0.05
    
    # ML Models
    USE_ML_RANKING: bool = True
    ML_MODEL_PATH: str = "ml_models/ranking/xgboost_ranker.json"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "txt"]
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if isinstance(v, list):
            return v
        return [origin.strip() for origin in v.split(",")]
    
    @validator("ALLOWED_EXTENSIONS", pre=True)
    def parse_allowed_extensions(cls, v: str | List[str]) -> List[str]:
        """Parse allowed extensions from comma-separated string"""
        if isinstance(v, list):
            return v
        return [ext.strip() for ext in v.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
