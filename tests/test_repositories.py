import pytest
from unittest.mock import MagicMock, patch


class TestLinkRepository:
    def test_get_all(self):
        from app.repositories.link_repository import LinkRepository

        with patch("app.repositories.link_repository.get_session") as mock_session:
            mock_link = MagicMock()
            mock_link.to_dict.return_value = {"id": 1, "url": "https://example.com"}
            mock_link.project = None
            mock_query = MagicMock()
            mock_query.order_by.return_value.all.return_value = [mock_link]
            mock_session.return_value.query.return_value = mock_query

            result = LinkRepository.get_all()

            assert len(result) == 1
            assert result[0]["project_name"] == "Default"

    def test_get_all_with_project(self):
        from app.repositories.link_repository import LinkRepository

        with patch("app.repositories.link_repository.get_session") as mock_session:
            mock_link = MagicMock()
            mock_link.to_dict.return_value = {"id": 1, "url": "https://example.com"}
            mock_project = MagicMock()
            mock_project.name = "Test Project"
            mock_link.project = mock_project
            mock_query = MagicMock()
            mock_query.order_by.return_value.all.return_value = [mock_link]
            mock_session.return_value.query.return_value = mock_query

            result = LinkRepository.get_all()

            assert result[0]["project_name"] == "Test Project"

    def test_get_all_with_project_filter(self):
        from app.repositories.link_repository import LinkRepository

        with patch("app.repositories.link_repository.get_session") as mock_session:
            mock_link = MagicMock()
            mock_link.to_dict.return_value = {"id": 1}
            mock_link.project = None
            mock_query = MagicMock()
            mock_query.filter.return_value.order_by.return_value.all.return_value = [
                mock_link
            ]
            mock_session.return_value.query.return_value = mock_query

            result = LinkRepository.get_all(project_id=1)

            mock_query.filter.assert_called_once()

    def test_get_by_id(self):
        from app.repositories.link_repository import LinkRepository

        with patch("app.repositories.link_repository.get_session") as mock_session:
            mock_link = MagicMock()
            mock_link.to_dict.return_value = {"id": 1}
            mock_link.project = None
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_link
            mock_session.return_value.query.return_value = mock_query

            result = LinkRepository.get_by_id(1)

            assert result["id"] == 1
            assert result["project_name"] == "Default"

    def test_get_by_id_not_found(self):
        from app.repositories.link_repository import LinkRepository

        with patch("app.repositories.link_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            result = LinkRepository.get_by_id(999)

            assert result is None

    def test_create(self):
        from app.repositories.link_repository import LinkRepository

        with patch("app.repositories.link_repository.get_session") as mock_session:
            mock_link = MagicMock()
            mock_link.to_dict.return_value = {"id": 1, "url": "https://example.com"}
            mock_session.return_value.add = MagicMock()
            mock_session.return_value.commit = MagicMock()
            mock_session.return_value.refresh = MagicMock()

            result = LinkRepository.create("https://example.com", "Example")

            mock_session.return_value.add.assert_called_once()
            mock_session.return_value.commit.assert_called_once()

    def test_update(self):
        from app.repositories.link_repository import LinkRepository

        with patch("app.repositories.link_repository.get_session") as mock_session:
            mock_link = MagicMock()
            mock_link.to_dict.return_value = {"id": 1}
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_link
            mock_session.return_value.query.return_value = mock_query

            result = LinkRepository.update(1, title="Updated")

            mock_session.return_value.commit.assert_called_once()

    def test_update_not_found(self):
        from app.repositories.link_repository import LinkRepository

        with patch("app.repositories.link_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            result = LinkRepository.update(999, title="Updated")

            assert result is None

    def test_delete(self):
        from app.repositories.link_repository import LinkRepository
        from app.repositories import diff_repository

        with patch("app.repositories.link_repository.get_session") as mock_session:
            mock_link = MagicMock()
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_link
            mock_session.return_value.query.return_value = mock_query

            with (
                patch.object(diff_repository.InitialPageRepository, "delete_by_link"),
                patch.object(diff_repository.DiffRepository, "delete_by_link"),
            ):
                result = LinkRepository.delete(1)

            mock_session.return_value.commit.assert_called()

    def test_delete_not_found(self):
        from app.repositories.link_repository import LinkRepository

        with patch("app.repositories.link_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            result = LinkRepository.delete(999)

            assert result is False


class TestProjectRepository:
    def test_get_all(self):
        from app.repositories.project_repository import ProjectRepository

        with patch("app.repositories.project_repository.get_session") as mock_session:
            mock_project = MagicMock()
            mock_project.to_dict.return_value = {"id": 1, "name": "Test"}
            mock_query = MagicMock()
            mock_query.order_by.return_value.all.return_value = [mock_project]
            mock_session.return_value.query.return_value = mock_query

            result = ProjectRepository.get_all()

            assert len(result) == 1

    def test_get_by_id(self):
        from app.repositories.project_repository import ProjectRepository

        with patch("app.repositories.project_repository.get_session") as mock_session:
            mock_project = MagicMock()
            mock_project.to_dict.return_value = {"id": 1}
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_project
            mock_session.return_value.query.return_value = mock_query

            result = ProjectRepository.get_by_id(1)

            assert result["id"] == 1

    def test_get_by_id_not_found(self):
        from app.repositories.project_repository import ProjectRepository

        with patch("app.repositories.project_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            result = ProjectRepository.get_by_id(999)

            assert result is None

    def test_create(self):
        from app.repositories.project_repository import ProjectRepository

        with patch("app.repositories.project_repository.get_session") as mock_session:
            mock_project = MagicMock()
            mock_project.to_dict.return_value = {"id": 1, "name": "Test"}
            mock_session.return_value.add = MagicMock()
            mock_session.return_value.commit = MagicMock()
            mock_session.return_value.refresh = MagicMock()

            result = ProjectRepository.create("Test Project", "Description")

            mock_session.return_value.add.assert_called_once()
            mock_session.return_value.commit.assert_called_once()

    def test_delete(self):
        from app.repositories.project_repository import ProjectRepository

        with patch("app.repositories.project_repository.get_session") as mock_session:
            mock_project = MagicMock()
            mock_project.id = 2
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_project
            mock_session.return_value.query.return_value = mock_query

            result = ProjectRepository.delete(2)

            mock_session.return_value.delete.assert_called_once()
            mock_session.return_value.commit.assert_called()

    def test_delete_default_project(self):
        from app.repositories.project_repository import ProjectRepository

        with patch("app.repositories.project_repository.get_session") as mock_session:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_project
            mock_session.return_value.query.return_value = mock_query

            result = ProjectRepository.delete(1)

            assert result is False

    def test_delete_not_found(self):
        from app.repositories.project_repository import ProjectRepository

        with patch("app.repositories.project_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            result = ProjectRepository.delete(999)

            assert result is False
