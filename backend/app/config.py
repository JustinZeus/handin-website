from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    admin_token: str
    site_title: str = "Untitled Site"
    data_dir: str = "./data"
    max_upload_bytes: int = 100_000_000
    allowed_upload_types: str = "pdf,png,jpg,jpeg,gif,mp4,webm,mp3,wav,ogg,webp"

    model_config = {"env_prefix": "HANDIN_"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
