import pytest
from unittest.mock import MagicMock, patch


class TestHistoryRepository:
    def test_get_by_link(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_history = MagicMock()
            mock_history.to_dict.return_value = {"id": 1}
            mock_query = MagicMock()
            mock_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
                mock_history
            ]
            mock_session.return_value.query.return_value = mock_query

            result = HistoryRepository.get_by_link(1)

            assert len(result) == 1

    def test_get_oldest(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_history = MagicMock()
            mock_history.to_dict.return_value = {"id": 1}
            mock_query = MagicMock()
            mock_query.filter_by.return_value.order_by.return_value.first.return_value = mock_history
            mock_session.return_value.query.return_value = mock_query

            result = HistoryRepository.get_oldest(1)

            assert result["id"] == 1

    def test_get_oldest_not_found(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.order_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            result = HistoryRepository.get_oldest(999)

            assert result is None

    def test_get_by_id(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_history = MagicMock()
            mock_history.to_dict.return_value = {"id": 1}
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_history
            mock_session.return_value.query.return_value = mock_query

            result = HistoryRepository.get_by_id(1)

            assert result["id"] == 1

    def test_get_by_id_not_found(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            result = HistoryRepository.get_by_id(999)

            assert result is None

    def test_get_previous(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_history = MagicMock()
            mock_history.to_dict.return_value = {"id": 1}
            mock_query = MagicMock()
            mock_query.filter.return_value.order_by.return_value.first.return_value = (
                mock_history
            )
            mock_session.return_value.query.return_value = mock_query

            result = HistoryRepository.get_previous(1, 2)

            assert result is not None

    def test_get_previous_not_found(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter.return_value.order_by.return_value.first.return_value = (
                None
            )
            mock_session.return_value.query.return_value = mock_query

            result = HistoryRepository.get_previous(1, 999)

            assert result is None

    def test_get_baseline(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_history = MagicMock()
            mock_history.to_dict.return_value = {"id": 1}
            mock_query = MagicMock()
            mock_query.filter_by.return_value.order_by.return_value.first.return_value = mock_history
            mock_session.return_value.query.return_value = mock_query

            result = HistoryRepository.get_baseline(1)

            assert result["id"] == 1

    def test_is_initial_entry(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_history = MagicMock()
            mock_history.id = 1
            mock_query = MagicMock()
            mock_query.filter_by.return_value.order_by.return_value.first.return_value = mock_history
            mock_session.return_value.query.return_value = mock_query

            result = HistoryRepository.is_initial_entry(1, 1)

            assert result is True

    def test_is_initial_entry_not_first(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_history = MagicMock()
            mock_history.id = 1
            mock_query = MagicMock()
            mock_query.filter_by.return_value.order_by.return_value.first.return_value = mock_history
            mock_session.return_value.query.return_value = mock_query

            result = HistoryRepository.is_initial_entry(1, 2)

            assert result is False

    def test_is_initial_entry_no_history(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter_by.return_value.order_by.return_value.first.return_value = None
            mock_session.return_value.query.return_value = mock_query

            result = HistoryRepository.is_initial_entry(1, 1)

            assert result is None or result is False

    def test_create(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_history = MagicMock()
            mock_history.to_dict.return_value = {"id": 1}
            mock_session.return_value.add = MagicMock()
            mock_session.return_value.commit = MagicMock()
            mock_session.return_value.refresh = MagicMock()

            with patch.object(
                HistoryRepository, "_trim_old_history", return_value=None
            ):
                result = HistoryRepository.create(1, "content", "hash")

            mock_session.return_value.add.assert_called_once()
            mock_session.return_value.commit.assert_called()

    def test_update_screenshot(self):
        from app.repositories.history_repository import HistoryRepository

        with patch("app.repositories.history_repository.get_session") as mock_session:
            mock_history = MagicMock()
            mock_query = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_history
            mock_session.return_value.query.return_value = mock_query

            HistoryRepository.update_screenshot(1, "test.png")

            mock_session.return_value.commit.assert_called_once()
