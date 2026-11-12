"""Settings loaded from environment variables (see api/.env.example)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    jwt_audience: str = "authenticated"
    cors_origins: str = "http://localhost:3000"
    internal_api_key: str = ""
    demo_user_password: str = ""
    scheduler_enabled: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def require(self) -> None:
        """Fail fast at startup when a required variable is missing."""
        missing = [] if self.database_url else ["database_url"]
        if not (self.supabase_jwt_secret or self.supabase_url):
            missing.append("supabase_jwt_secret or supabase_url")
        if missing:
            raise RuntimeError(f"Missing required settings: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
