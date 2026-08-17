"""VaultShift Configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    VAULTSHIFT_DATA_DIR: str = "./data"
    VAULTSHIFT_CONFIG_DIR: str = "./config"
    VAULTSHIFT_LOG_LEVEL: str = "INFO"
    VAULTSHIFT_MAX_WORKERS: int = 2
    VAULTSHIFT_HOST: str = "0.0.0.0"
    VAULTSHIFT_PORT: int = 8501
    VAULTSHIFT_ALLOWED_PATHS: Optional[list[str]] = None
    VAULTSHIFT_HASH_CHUNK_SIZE: int = 67108864  # 64MB
    VAULTSHIFT_PARTIAL_EXT: str = ".vaultshift-partial"
    VAULTSHIFT_VERSION: str = "0.1.0"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
