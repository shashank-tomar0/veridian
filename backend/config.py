from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Keys
    groq_api_key: str | None = None
    tavily_api_key: str | None = None
    claimbuster_api_key: str | None = None
    huggingface_hub_token: str | None = None
    hf_token: str | None = None
    whatsapp_api_token: str | None = None
    whatsapp_verify_token: str | None = None
    telegram_bot_token: str | None = None

    # Database URLs
    database_url: str = "postgresql+asyncpg://veridian:password@localhost:5432/veridian"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    qdrant_url: str = "http://localhost:6333"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_media_bucket: str = "veridian-media"

    # Security
    jwt_secret_key: str = "replace_me_in_production_super_secret"
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
