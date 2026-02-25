from typing import Dict

from app.repositories import ProjectRepository, LinkRepository, HistoryRepository
from app.extensions import check_database_health


class HealthService:
    @staticmethod
    def get_status() -> Dict[str, str]:
        status: Dict[str, str] = {
            "backend": "healthy",
            "database": "healthy",
            "llm": "disconnected",
        }

        if not check_database_health():
            status["database"] = "error"
            status["backend"] = "degraded"

        from flask import current_app

        if current_app.config.get("LLM_API_KEY"):
            status["llm"] = "connected"

        return status
