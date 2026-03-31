from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "TOKEN_FORECAST_"}

    port: int = 8000
    host: str = "0.0.0.0"
    budget_monthly: float = 0.0
    db_path: str = "./data/token_forecast.db"
    forecast_days: int = 30


settings = Settings()
