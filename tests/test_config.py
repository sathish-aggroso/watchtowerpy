import os
import pytest
from unittest.mock import patch, MagicMock


class TestConfig:
    def test_config_values(self):
        from app.config import Config

        assert Config.SECRET_KEY is not None
        assert Config.DATABASE_PATH is not None
        assert Config.SQLALCHEMY_DATABASE_URI is not None
        assert Config.SQLALCHEMY_TRACK_MODIFICATIONS is False
        assert Config.PORT is not None
        assert Config.LLM_MODEL == "MiniMax-M2.5"
        assert Config.LLM_PROVIDER == "minimax"


class TestDevelopmentConfig:
    def test_development_config(self):
        from app.config import DevelopmentConfig

        assert DevelopmentConfig.DEBUG is True
        assert hasattr(DevelopmentConfig, "SECRET_KEY")


class TestProductionConfig:
    def test_production_config(self):
        from app.config import ProductionConfig

        assert ProductionConfig.DEBUG is False


class TestConfigMap:
    def test_config_map(self):
        from app.config import config_map, DevelopmentConfig, ProductionConfig

        assert config_map["development"] == DevelopmentConfig
        assert config_map["production"] == ProductionConfig
        assert config_map["default"] == DevelopmentConfig
