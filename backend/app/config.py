from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="allow")
    
    # Environment
    ENV: str = Field(default="dev")
    LOG_LEVEL: str = Field(default="INFO")
    
    # Database
    MONGO_URL: str = Field(default="mongodb://localhost:27017")
    DB_NAME: str = Field(default="extrema_db")
    
    # External APIs
    HELIUS_API_KEY: str | None = Field(default=None)
    
    # Signal detection defaults
    ATR_MIN: float = 0.6
    VOLZ_MIN: float = 1.0
    BBW_MIN: float = 0.005
    BREAKOUT_ATR_MULT: float = 0.5
    VOL_MULT: float = 1.5
    CONFIRM_WINDOW: int = 6
    
    # Microstructure thresholds
    MICRO_IMB: float = 0.15  # Ladder imbalance threshold
    SPREAD_BPS_MAX: float = 10.0  # Max spread in basis points
    OBV_Z_VETO: float = 2.0  # OBV z-score veto threshold
    ENABLE_MICRO_GATE: bool = True  # Enable microstructure gating
    
    # CORS
    CORS_ORIGINS: str = "*"

settings = Settings()