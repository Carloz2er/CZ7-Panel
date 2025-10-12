from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CZ7 Host"
    PROJECT_VERSION: str = "0.1.0"

    # Discord OAuth
    DISCORD_CLIENT_ID: str
    DISCORD_CLIENT_SECRET: str

    # Session
    SESSION_SECRET: str

    # Database
    DATABASE_URL: str


    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()