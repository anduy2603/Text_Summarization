from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vietnamese Text Summarization"
    app_version: str = "0.1.0"
    app_env: str = "dev"
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Input subsystem (Phase 2)
    input_max_file_bytes: int = 10 * 1024 * 1024
    input_allowed_extensions: str = ".txt,.docx,.pdf"
    input_url_timeout_sec: float = 20.0
    input_url_max_bytes: int = 5 * 1024 * 1024
    input_url_user_agent: str = "VietSumInputBot/0.1 (+local dev)"
    input_url_allow_private_hosts: bool = False
    input_min_text_chars: int = 1
    input_max_text_chars: int = 1_000_000

    @cached_property
    def input_allowed_extensions_set(self) -> set[str]:
        return {
            ext.strip().lower()
            for ext in self.input_allowed_extensions.split(",")
            if ext.strip()
        }

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
