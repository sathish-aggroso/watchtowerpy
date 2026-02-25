import pytest
from unittest.mock import MagicMock, patch


class TestHealthService:
    def test_get_status_healthy(self):
        from app.services.health_service import HealthService
        from flask import Flask

        app = Flask(__name__)
        app.config["LLM_API_KEY"] = "test-key"

        with app.app_context():
            from app.extensions import check_database_health

            with patch(
                "app.services.health_service.check_database_health", return_value=True
            ):
                status = HealthService.get_status()

                assert status["backend"] == "healthy"
                assert status["database"] == "healthy"
                assert status["llm"] == "connected"


class TestLinkService:
    def test_get_all_links(self):
        from app.services.link_service import LinkService

        with patch("app.services.link_service.LinkRepository") as mock_repo:
            mock_repo.get_all.return_value = [{"id": 1, "url": "https://example.com"}]

            result = LinkService.get_all_links()

            assert len(result) == 1
            assert result[0]["url"] == "https://example.com"

    def test_get_link(self):
        from app.services.link_service import LinkService

        with patch("app.services.link_service.LinkRepository") as mock_repo:
            mock_repo.get_by_id.return_value = {"id": 1, "url": "https://example.com"}

            result = LinkService.get_link(1)

            assert result["id"] == 1

    def test_create_link(self):
        from app.services.link_service import LinkService

        with patch("app.services.link_service.LinkRepository") as mock_repo:
            mock_repo.create.return_value = {"id": 1, "url": "https://example.com"}

            result = LinkService.create_link("https://example.com")

            assert result["id"] == 1

    def test_delete_link(self):
        from app.services.link_service import LinkService

        with patch("app.services.link_service.LinkRepository") as mock_repo:
            mock_repo.delete.return_value = True

            result = LinkService.delete_link(1)

            assert result is True


class TestProjectService:
    def test_get_all_projects(self):
        from app.services.project_service import ProjectService

        with patch("app.services.project_service.ProjectRepository") as mock_repo:
            mock_repo.get_all.return_value = [{"id": 1, "name": "Test"}]

            result = ProjectService.get_all_projects()

            assert len(result) == 1
            assert result[0]["name"] == "Test"

    def test_create_project(self):
        from app.services.project_service import ProjectService

        with patch("app.services.project_service.ProjectRepository") as mock_repo:
            mock_repo.create.return_value = {"id": 1, "name": "New Project"}

            result = ProjectService.create_project("New Project")

            assert result["name"] == "New Project"

    def test_delete_project(self):
        from app.services.project_service import ProjectService

        with patch("app.services.project_service.ProjectRepository") as mock_repo:
            mock_repo.delete.return_value = True

            result = ProjectService.delete_project(1)

            assert result is True
