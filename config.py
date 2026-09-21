from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field , SecretStr

class Settings(BaseSettings):
    openrouter_api_key: SecretStr
    model: str =Field(default="nvidia/nemotron-3.5-lightning:free")
    model_config = SettingsConfigDict(env_file=".env")
settings = Settings()