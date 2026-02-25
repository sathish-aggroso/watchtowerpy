import pytest
from unittest.mock import MagicMock, patch


class TestInitialPageRepository:
    def test_get_by_link(self):
        from app.repositories.diff_repository import InitialPageRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_initial = MagicMock()
            mock_initial.to_dict.return_value = {"id": 1, "link_id": 1}
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_initial
            mock_session.return_value.query.return_value = mock_query

            result = InitialPageRepository.get_by_link(1)

            assert result["id"] == 1
            mock_session.return_value.close.assert_called()

    def test_get_by_link_not_found(self):
        from app.repositories.diff_repository import InitialPageRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            result = InitialPageRepository.get_by_link(999)

            assert result is None

    def test_create(self):
        from app.repositories.diff_repository import InitialPageRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_initial = MagicMock()
            mock_initial.to_dict.return_value = {"id": 1, "link_id": 1}
            mock_session.return_value.add = MagicMock()
            mock_session.return_value.commit = MagicMock()
            mock_session.return_value.refresh = MagicMock()

            result = InitialPageRepository.create(1, "content", "hash123")

            mock_session.return_value.add.assert_called_once()
            mock_session.return_value.commit.assert_called_once()

    def test_update_screenshot(self):
        from app.repositories.diff_repository import InitialPageRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_initial = MagicMock()
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_initial
            mock_session.return_value.query.return_value = mock_query

            InitialPageRepository.update_screenshot(1, "test.png")

            mock_session.return_value.commit.assert_called_once()

    def test_update_screenshot_not_found(self):
        from app.repositories.diff_repository import InitialPageRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            InitialPageRepository.update_screenshot(999, "test.png")

            mock_session.return_value.commit.assert_not_called()

    def test_delete_by_link(self):
        from app.repositories.diff_repository import InitialPageRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_session.return_value.query.return_value = mock_query
            mock_query.filter_by.return_value.delete = MagicMock()

            InitialPageRepository.delete_by_link(1)

            mock_session.return_value.commit.assert_called_once()


class TestDiffRepository:
    def test_get_by_link(self):
        from app.repositories.diff_repository import DiffRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_diff = MagicMock()
            mock_diff.to_dict.return_value = {"id": 1}
            mock_query = MagicMock()
            mock_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
                mock_diff
            ]
            mock_session.return_value.query.return_value = mock_query

            result = DiffRepository.get_by_link(1)

            assert len(result) == 1

    def test_get_by_id(self):
        from app.repositories.diff_repository import DiffRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_diff = MagicMock()
            mock_diff.to_dict.return_value = {"id": 1}
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_diff
            mock_session.return_value.query.return_value = mock_query

            result = DiffRepository.get_by_id(1)

            assert result["id"] == 1

    def test_get_by_id_not_found(self):
        from app.repositories.diff_repository import DiffRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            result = DiffRepository.get_by_id(999)

            assert result is None

    def test_get_latest(self):
        from app.repositories.diff_repository import DiffRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_diff = MagicMock()
            mock_diff.to_dict.return_value = {"id": 1}
            mock_query = MagicMock()
            mock_query.filter_by.return_value.order_by.return_value.first.return_value = mock_diff
            mock_session.return_value.query.return_value = mock_query

            result = DiffRepository.get_latest(1)

            assert result["id"] == 1

    def test_get_latest_not_found(self):
        from app.repositories.diff_repository import DiffRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.order_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            result = DiffRepository.get_latest(999)

            assert result is None

    def test_get_previous(self):
        from app.repositories.diff_repository import DiffRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_diff = MagicMock()
            mock_diff.previous_diff_id = 1
            mock_diff.to_dict.return_value = {"id": 1}
            mock_prev = MagicMock()
            mock_prev.to_dict.return_value = {"id": 2}
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_diff
            mock_session.return_value.query.return_value = mock_query
            mock_session.return_value.query.filter_by.return_value.first.return_value = mock_prev

            result = DiffRepository.get_previous(1)

            assert result is not None

    def test_get_previous_no_previous(self):
        from app.repositories.diff_repository import DiffRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_diff = MagicMock()
            mock_diff.previous_diff_id = None
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_diff
            mock_session.return_value.query.return_value = mock_query

            result = DiffRepository.get_previous(1)

            assert result is None

    def test_create(self):
        from app.repositories.diff_repository import DiffRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_diff = MagicMock()
            mock_diff.to_dict.return_value = {"id": 1}
            mock_session.return_value.add = MagicMock()
            mock_session.return_value.commit = MagicMock()
            mock_session.return_value.refresh = MagicMock()

            result = DiffRepository.create(1, None, "content", "hash")

            mock_session.return_value.add.assert_called_once()
            mock_session.return_value.commit.assert_called_once()

    def test_update_screenshot(self):
        from app.repositories.diff_repository import DiffRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_diff = MagicMock()
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_diff
            mock_session.return_value.query.return_value = mock_query

            DiffRepository.update_screenshot(1, "test.png")

            mock_session.return_value.commit.assert_called_once()

    def test_delete_by_link(self):
        from app.repositories.diff_repository import DiffRepository

        with patch("app.repositories.diff_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_session.return_value.query.return_value = mock_query
            mock_query.filter_by.return_value.delete = MagicMock()

            DiffRepository.delete_by_link(1)

            mock_session.return_value.commit.assert_called_once()
