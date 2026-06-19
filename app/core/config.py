from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    JWT_SECRET: str
    JWT_ALG: str = "HS256"

    class Config:
        env_file = ".env"
        extra = "ignore"  # ignora las demas variables del .env (PORT, LOG_LEVEL, etc.)

settings = Settings()