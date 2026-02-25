import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestHistoryService:
    def test_get_link_history(self):
        from app.services.history_service import HistoryService
        from app.repositories import history_repository

        with patch.object(
            history_repository.HistoryRepository, "get_by_link"
        ) as mock_get:
            mock_get.return_value = [{"id": 1}]

            result = HistoryService.get_link_history(1)

            assert len(result) == 1

    def test_get_history_not_found(self):
        from app.services.history_service import HistoryService
        from app.repositories import history_repository

        with patch.object(
            history_repository.HistoryRepository, "get_by_id"
        ) as mock_get:
            mock_get.return_value = None

            result = HistoryService.get_history(1)

            assert result is None

    def test_get_history_initial_entry(self):
        from app.services.history_service import HistoryService
        from app.repositories import history_repository, link_repository

        with (
            patch.object(
                history_repository.HistoryRepository, "get_by_id"
            ) as mock_get_id,
            patch.object(
                history_repository.HistoryRepository, "is_initial_entry"
            ) as mock_is_initial,
            patch.object(link_repository.LinkRepository, "get_by_id") as mock_link,
        ):
            mock_get_id.return_value = {
                "id": 1,
                "link_id": 1,
                "content": "test",
            }
            mock_is_initial.return_value = True
            mock_link.return_value = {"id": 1, "url": "https://example.com"}

            result = HistoryService.get_history(1)

            assert result is not None
            assert result["is_initial"] is True

    def test_get_history_with_previous(self):
        from app.services.history_service import HistoryService
        from app.repositories import history_repository, link_repository
        from app.services import check_service

        with (
            patch.object(
                history_repository.HistoryRepository, "get_by_id"
            ) as mock_get_id,
            patch.object(
                history_repository.HistoryRepository, "is_initial_entry"
            ) as mock_is_initial,
            patch.object(
                history_repository.HistoryRepository, "get_previous"
            ) as mock_prev,
            patch.object(link_repository.LinkRepository, "get_by_id") as mock_link,
            patch.object(check_service.CheckService, "_compute_diff") as mock_diff,
            patch.object(
                check_service.CheckService, "_compute_html_diff"
            ) as mock_html_diff,
            patch.object(
                check_service.CheckService, "_generate_paragraph_diff"
            ) as mock_para,
            patch.object(
                check_service.CheckService, "_generate_code_diff"
            ) as mock_code,
            patch.object(
                check_service.CheckService, "_compute_image_diff"
            ) as mock_image,
            patch("bs4.BeautifulSoup") as mock_soup,
        ):
            mock_get_id.return_value = {
                "id": 2,
                "link_id": 1,
                "content": "<html><body>New</body></html>",
            }
            mock_is_initial.return_value = False
            mock_prev.return_value = {"content": "<html><body>Old</body></html>"}
            mock_link.return_value = {"id": 1, "url": "https://example.com"}
            mock_diff.return_value = "diff text"
            mock_html_diff.return_value = "<html>diff</html>"
            mock_para.return_value = "<html>paragraph</html>"
            mock_code.return_value = "<div>code</div>"
            mock_image.return_value = {"added": [], "removed": []}

            mock_body_old = MagicMock()
            mock_body_new = MagicMock()
            mock_body_old.get_text.return_value = "old text"
            mock_body_new.get_text.return_value = "new text"

            mock_soup_instance_old = MagicMock()
            mock_soup_instance_new = MagicMock()
            mock_soup_instance_old.find.return_value = mock_body_old
            mock_soup_instance_new.find.return_value = mock_body_new
            mock_soup.side_effect = [mock_soup_instance_old, mock_soup_instance_new]

            result = HistoryService.get_history(2)

            assert result is not None
            assert result["is_initial"] is False
