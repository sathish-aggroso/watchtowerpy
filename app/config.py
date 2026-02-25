import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "./db/checkdiff.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PORT = int(os.environ.get("PORT", 5000))

    LLM_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    LLM_MODEL = os.environ.get("LLM_MODEL", "gemma-3-27b-it")
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
