from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CZ7 Host"
    PROJECT_VERSION: str = "0.1.0"

    # Discord OAuth
    DISCORD_CLIENT_ID: str = "YOUR_CLIENT_ID_HERE"
    DISCORD_CLIENT_SECRET: str = "YOUR_CLIENT_SECRET_HERE"

    # Session
    SESSION_SECRET: str = "a_secure_random_string"


    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()