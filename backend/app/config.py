from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")
    
    ENV: str = Field(default="dev")
    LOG_LEVEL: str = Field(default="INFO")
    # data / signal defaults
    ATR_MIN: float = 0.6
    VOLZ_MIN: float = 1.0
    BBW_MIN: float = 0.005
    BREAKOUT_ATR_MULT: float = 0.5
    VOL_MULT: float = 1.5
    CONFIRM_WINDOW: int = 6
    # CORS
    CORS_ORIGINS: str = "*"

settings = Settings()