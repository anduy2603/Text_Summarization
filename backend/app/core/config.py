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

    # Model lifecycle
    preload_models: bool = True

    # Summarization subsystem (Phase 3) — product defaults (overridable per request for experiments)
    summary_engine: str = "hybrid"
    summary_max_sentences: int = 3

    # TextRank selection
    textrank_mmr_lambda: float = 0.7
    textrank_position_bias: float = 0.20

    # Hybrid (TextRank preselect → ViT5 rewrite; never pure ViT5 on full upload)
    hybrid_preselect_multiplier: float = 2.0
    hybrid_preselect_cap: int = 12
    hybrid_preselect_floor_short: int = 4
    hybrid_preselect_floor_medium: int = 6
    hybrid_preselect_floor_long: int = 8
    hybrid_vit5_min_chars: int = 600
    hybrid_long_doc_chars: int = 12_000
    hybrid_chunk_chars: int = 4_000
    hybrid_min_summary_chars: int = 280

    # ViT5 abstractive (VietNews fine-tune)
    vit5_model_name: str = "VietAI/vit5-base-vietnews-summarization"
    vit5_max_input_tokens: int = 512
    vit5_max_new_tokens: int = 256
    vit5_tokens_per_sentence: int = 64
    vit5_num_beams: int = 4
    # Hybrid lead only: short abstractive opener, no min_new_tokens / length_penalty
    vit5_lead_max_sentences: int = 2
    vit5_lead_max_chars: int = 420
    vit5_lead_max_weird_char_ratio: float = 0.06
    vit5_lead_max_repetition_rate: float = 0.35

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
