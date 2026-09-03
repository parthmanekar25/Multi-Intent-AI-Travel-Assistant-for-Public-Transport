"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    lta_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    cache_ttl_seconds: int = 60
    bus_services_cache_ttl_seconds: int = 86_400
    bus_stops_cache_ttl_seconds: int = 86_400
    request_timeout_seconds: float = 10.0
    timezone: str = "Asia/Singapore"
    lta_base_url: str = "https://datamall2.mytransport.sg/ltaodataservice"
    weather_url: str = (
        "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
