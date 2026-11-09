from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str
    PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()  # type: ignore[call-arg]