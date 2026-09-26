import os
from typing import List, Union, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SentinelVoice"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Execution mode: 'production', 'development', 'demo'
    APP_MODE: str = Field(default="development", description="Runtime application mode: production, development, or demo")
    
    # Canonical secret key for signing JWT tokens and hashes
    SECRET_KEY: str = Field(
        default="sentinelvoice-insecure-dev-secret-key-change-in-prod-32bytes",
        description="HMAC secret key for authentication tokens. Must be securely set in production."
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./sentinelvoice.db",
        description="Database connection string. Production requires PostgreSQL."
    )
    
    # Optional Redis for rate limiting and streaming pub/sub
    REDIS_URL: Optional[str] = None
    
    # AI Provider Selection: 'azure', 'local', or 'demo'
    AI_PROVIDER: str = Field(default="local", description="Primary AI provider: local, azure, or demo")
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    
    # Azure AI Speech
    AZURE_SPEECH_ENDPOINT: str = ""
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "eastus"
    
    # Azure AI Language
    AZURE_LANGUAGE_ENDPOINT: str = ""
    AZURE_LANGUAGE_KEY: str = ""
    
    # Audio Security & Upload Constraints
    MAX_AUDIO_SIZE_MB: int = 25
    MAX_AUDIO_DURATION_SECONDS: int = 300  # 5 minutes max upload
    TEMP_UPLOAD_DIR: str = "temp_audio"
    
    # Privacy & Retention: Default OFF (no raw audio retention)
    ENABLE_RAW_AUDIO_RETENTION: bool = False
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 120
    
    # CORS Configuration
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped.startswith("["):
                return [i.strip() for i in v_stripped.split(",") if i.strip()]
        return v

    @field_validator("APP_MODE", mode="before")
    @classmethod
    def normalize_mode(cls, v: str) -> str:
        if isinstance(v, str):
            val = v.strip().lower()
            if val in ("prod", "production"):
                return "production"
            elif val in ("dev", "development"):
                return "development"
            elif val in ("demo", "test", "testing"):
                return "demo"
        return v

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        """
        Enforce strict production startup invariants:
        - Must NOT use SQLite in production.
        - Must NOT use default insecure SECRET_KEY in production.
        - Must NOT have wildcard '*' CORS origins in production.
        - Must configure valid provider credentials if AI_PROVIDER is 'azure'.
        """
        if self.APP_MODE == "production":
            # 1. Database check
            if "sqlite" in self.DATABASE_URL.lower():
                raise ValueError(
                    "[FATAL CONFIGURATION ERROR] SQLite cannot be used in production mode. "
                    "Configure a valid PostgreSQL connection string via DATABASE_URL."
                )
            
            # 2. Secret Key check
            if "insecure" in self.SECRET_KEY.lower() or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "[FATAL CONFIGURATION ERROR] Insecure or default SECRET_KEY detected in production. "
                    "Configure a cryptographically secure 32+ character SECRET_KEY."
                )
            
            # 3. CORS check
            if isinstance(self.CORS_ORIGINS, list):
                if "*" in self.CORS_ORIGINS:
                    raise ValueError(
                        "[FATAL CONFIGURATION ERROR] Wildcard '*' CORS origin is forbidden in production. "
                        "Specify exact trusted frontend domains in CORS_ORIGINS."
                    )
                if not self.CORS_ORIGINS:
                    raise ValueError(
                        "[FATAL CONFIGURATION ERROR] CORS_ORIGINS cannot be empty in production."
                    )
            
            # 4. Azure credentials check if configured as primary
            if self.AI_PROVIDER == "azure":
                if not self.AZURE_OPENAI_ENDPOINT or not self.AZURE_OPENAI_API_KEY:
                    raise ValueError(
                        "[FATAL CONFIGURATION ERROR] AI_PROVIDER is set to 'azure' but AZURE_OPENAI_ENDPOINT "
                        "or AZURE_OPENAI_API_KEY is missing."
                    )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
