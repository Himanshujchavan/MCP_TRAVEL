from pydantic import BaseSettings

class Settings(BaseSettings):
    MCP_SERVER_URL: str
    SKYSCANNER_API_KEY: str
    BOOKING_API_KEY: str
    WEATHER_API_KEY: str
    GOOGLE_PLACES_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
