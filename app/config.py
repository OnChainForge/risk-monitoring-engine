from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    log_level: str = "INFO"
    ethereum_rpc_url: str

    class Config:
        env_file = ".env"


settings = Settings()
