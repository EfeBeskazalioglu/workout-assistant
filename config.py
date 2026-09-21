from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field , SecretStr

class Settings(BaseSettings):
    llm_api_key: SecretStr
    llm_model: str
    llm_base_url: str
    timeout: float = Field(default=15)
    model_config = SettingsConfigDict(env_file=".env")
settings = Settings()