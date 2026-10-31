from functools import lru_cache
from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='../.env', extra='ignore')
    database_url: str = 'postgresql+psycopg://ai_dmc:ai_dmc@localhost:5432/ai_dmc'
    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = Field(default=60, ge=1)
    storage_dir: Path = Path('../storage')
    pipeline_mode: str = 'mock'
    pipeline_import: str = 'app.integrations.real:process_document'
    ollama_host: str = 'http://localhost:11434'
    ollama_model: str = Field(default='gemma4:e4b', min_length=1)
    ollama_timeout: float = Field(default=180, gt=0)
    pipeline_votes: int = Field(default=3, ge=1)
    pipeline_temperature: float = 0.4
    pipeline_max_chars: int = Field(default=12000, gt=0)
    ocr_lang: str = 'id'
    ocr_dpi: int = Field(default=200, gt=0)
    ocr_max_pages: int = Field(default=5, gt=0)
    pdf_min_chars_per_page: int = Field(default=30, ge=0)
    taxonomy_path: Path = Path('../pipeline/config/taxonomy.json')
    confidence_threshold: float = Field(default=0.85, ge=0, le=1)
    cors_origins: str = 'http://localhost:3000'
    app_environment: str = 'development'
    seed_password: str | None = None

    @model_validator(mode='after')
    def validate_mode(self):
        if self.pipeline_mode not in {'mock', 'real'}:
            raise ValueError('PIPELINE_MODE harus mock atau real')
        if self.app_environment == 'production' and self.pipeline_mode == 'mock':
            raise ValueError('Mock tidak diizinkan pada production')
        return self


@lru_cache
def get_settings():
    return Settings()
