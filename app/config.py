from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL:str
    JAVA_API_BASE_URL:str
    
    class Config:
        env_file = ".env"
        
settings = Settings()
