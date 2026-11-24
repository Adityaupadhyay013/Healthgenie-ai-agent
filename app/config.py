from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "HealthGenie AI"
    ENVIRONMENT: str = "development"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    FRONTEND_URL: str = "http://localhost:5173"
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org/search"
    ENABLE_GEOCODING: bool = True
    HOSPITAL_SEARCH_RADIUS_KM: int = 15
    KIDNEY_MODEL_URL: str = ""
    LIVER_MODEL_URL: str = ""
    HEART_MODEL_URL: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
