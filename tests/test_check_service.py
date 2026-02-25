import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestCheckService:
    def test_compute_diff(self):
        from app.services.check_service import CheckService

        old_content = "line1\nline2\nline3"
        new_content = "line1\nline2 modified\nline3"

        result = CheckService._compute_diff(old_content, new_content)

        assert result is not None
        assert "line2" in result

    def test_compute_diff_no_old_content(self):
        from app.services.check_service import CheckService

        result = CheckService._compute_diff(None, "new content")

        assert result is None

    def test_compute_diff_no_changes(self):
        from app.services.check_service import CheckService

        content = "same content"
        result = CheckService._compute_diff(content, content)

        assert result is None

    def test_extract_price(self):
        from app.services.check_service import CheckService

        content = "<html><body>Price: $99.99</body></html>"

        result = CheckService._extract_price(content)

        assert result is not None

    def test_extract_price_usd(self):
        from app.services.check_service import CheckService

        content = "<html><body>99 USD</body></html>"

        result = CheckService._extract_price(content)

        assert result is not None

    def test_extract_price_euro(self):
        from app.services.check_service import CheckService

        content = "<html><body>€50.00</body></html>"

        result = CheckService._extract_price(content)

        assert result is not None

    def test_extract_price_no_price(self):
        from app.services.check_service import CheckService

        content = "<html><body>No price here</body></html>"

        result = CheckService._extract_price(content)

        assert result is None

    def test_extract_price_data_attribute(self):
        from app.services.check_service import CheckService

        content = '<html><body data-price="199">Test</body></html>'

        result = CheckService._extract_price(content)

        assert result is not None

    def test_generate_summary_simple(self):
        from app.services.check_service import CheckService

        diff_text = """--- old
+++ new
@@ -1 +1 @@
-old line
+new line
"""

        result = CheckService._generate_summary_simple(diff_text)

        assert result is not None
        assert "new line" in result or "line" in result.lower()

    def test_generate_summary_simple_no_diff(self):
        from app.services.check_service import CheckService

        result = CheckService._generate_summary_simple("")

        assert result == "No changes detected"

    def test_generate_body_diff(self):
        from app.services.check_service import CheckService
        from bs4 import BeautifulSoup

        old_soup = BeautifulSoup("<body><p>Old content</p></body>", "html.parser")
        new_soup = BeautifulSoup("<body><p>New content</p></body>", "html.parser")

        old_body = old_soup.find("body")
        new_body = new_soup.find("body")

        result = CheckService._generate_body_diff(old_body, new_body, "")

        assert result is not None
        assert "diff-added" in result or "diff-removed" in result

    def test_text_diff_to_html(self):
        from app.services.check_service import CheckService

        old_text = "old line"
        new_content = "new line"

        result = CheckService._text_diff_to_html(old_text, new_content)

        assert result is not None
        assert "<!DOCTYPE html>" in result

    def test_compute_html_diff_with_bodies(self):
        from app.services.check_service import CheckService

        old_content = "<html><body><p>Old</p></body></html>"
        new_content = "<html><body><p>New</p></body></html>"

        result = CheckService._compute_html_diff(old_content, new_content)

        assert result is not None

    def test_compute_html_diff_no_old(self):
        from app.services.check_service import CheckService

        result = CheckService._compute_html_diff(None, "new content")

        assert result is None

    def test_compute_html_diff_same_content(self):
        from app.services.check_service import CheckService

        content = "<html><body><p>Same</p></body></html>"

        result = CheckService._compute_html_diff(content, content)

        assert result is None

    def test_compute_html_diff_no_body(self):
        from app.services.check_service import CheckService

        old_content = "<html><head><title>Test</title></head></html>"
        new_content = "<html><head><title>Test</title></head></html>"

        result = CheckService._compute_html_diff(old_content, new_content)

        assert result is None

    def test_extract_images(self):
        from app.services.check_service import CheckService
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<html><body><img src="/image.png" alt="test"></body></html>',
            "html.parser",
        )

        result = CheckService._extract_images(soup, "https://example.com")

        assert len(result) == 1
        assert result[0]["src"] == "https://example.com/image.png"

    def test_extract_images_data_src(self):
        from app.services.check_service import CheckService
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<html><body><img data-src="/lazy.png"></body></html>', "html.parser"
        )

        result = CheckService._extract_images(soup, "https://example.com")

        assert len(result) == 1

    def test_compute_image_diff(self):
        from app.services.check_service import CheckService

        old_content = '<html><body><img src="/old.png"></body></html>'
        new_content = '<html><body><img src="/new.png"></body></html>'

        result = CheckService._compute_image_diff(
            old_content, new_content, "https://example.com"
        )

        assert "added" in result
        assert "removed" in result

    def test_compute_image_diff_no_url(self):
        from app.services.check_service import CheckService

        old_content = '<html><body><img src="/old.png"></body></html>'
        new_content = '<html><body><img src="/new.png"></body></html>'

        result = CheckService._compute_image_diff(old_content, new_content, None)

        assert result["added"] == []
        assert result["removed"] == []

    def test_generate_paragraph_diff(self):
        from app.services.check_service import CheckService
        from bs4 import BeautifulSoup

        old_soup = BeautifulSoup("<body><p>Old</p></body>", "html.parser")
        new_soup = BeautifulSoup("<body><p>New</p></body>", "html.parser")

        old_body = old_soup.find("body")
        new_body = new_soup.find("body")

        result = CheckService._generate_paragraph_diff(old_body, new_body, None)

        assert result is not None
        assert "<!DOCTYPE html>" in result

    def test_generate_code_diff(self):
        from app.services.check_service import CheckService

        old_content = "<html><body><p>Old</p></body></html>"
        new_content = "<html><body><p>New</p></body></html>"

        result = CheckService._generate_code_diff(old_content, new_content)

        assert result is not None
        assert "background: #1e1e1e" in result

    def test_escape_html(self):
        from app.services.check_service import _escape_html

        result = _escape_html("<>&'\"")

        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result

    def test_highlight_html_tags(self):
        from app.services.check_service import _highlight_html_tags

        result = _highlight_html_tags("<div>test</div>")

        assert result is not None


class TestCheckServiceLink:
    def test_check_link_not_found(self):
        from app.services.check_service import CheckService
        from app.repositories import link_repository

        with patch.object(link_repository, "LinkRepository") as mock_repo:
            mock_repo.get_by_id.return_value = None

            result = CheckService.check_link(999)

            assert result["success"] is False
            assert "not found" in result["error"]

    def test_check_link_fetch_failure(self):
        from app.services.check_service import CheckService
        from app.repositories import link_repository

        with (
            patch.object(link_repository, "LinkRepository") as mock_repo,
            patch.object(CheckService, "_fetch_url") as mock_fetch,
        ):
            mock_repo.get_by_id.return_value = {"id": 1, "url": "https://example.com"}
            mock_fetch.return_value = {"success": False, "error": "Connection error"}

            result = CheckService.check_link(1)

            assert result["success"] is False
            assert "error" in result


class TestCheckServiceFetchUrl:
    def test_fetch_url_with_pyppeteer_success(self):
        from app.services.check_service import CheckService

        with patch.object(CheckService, "_fetch_url_with_pyppeteer") as mock_pyppeteer:
            mock_pyppeteer.return_value = {
                "success": True,
                "content": "<html>Test</html>",
            }

            result = CheckService._fetch_url("https://example.com")

            assert result["success"] is True
            assert "content" in result

    def test_fetch_url_pyppeteer_fail_requests_success(self):
        from app.services.check_service import CheckService

        with (
            patch.object(CheckService, "_fetch_url_with_pyppeteer") as mock_pyppeteer,
            patch("requests.get") as mock_get,
        ):
            mock_pyppeteer.return_value = {"success": False, "error": "fail"}
            mock_response = MagicMock()
            mock_response.text = "<html>Test</html>"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = CheckService._fetch_url("https://example.com")

            assert result["success"] is True

    def test_fetch_url_exception(self):
        from app.services.check_service import CheckService

        with (
            patch.object(CheckService, "_fetch_url_with_pyppeteer") as mock_pyppeteer,
            patch("requests.get") as mock_get,
        ):
            mock_pyppeteer.return_value = {"success": False, "error": "fail"}
            mock_get.side_effect = Exception("Network error")

            result = CheckService._fetch_url("https://example.com")

            assert result["success"] is False


class TestCheckServiceFetch:
    def test_fetch_url_requests(self):
        from app.services.check_service import CheckService

        with (
            patch(
                "app.services.check_service.CheckService._fetch_url_with_pyppeteer"
            ) as mock_pyppeteer,
            patch("requests.get") as mock_get,
        ):
            mock_pyppeteer.return_value = {"success": False, "error": "fail"}
            mock_response = MagicMock()
            mock_response.text = "<html>Test</html>"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = CheckService._fetch_url("https://example.com")

            assert result["success"] is True
            assert "content" in result

    def test_fetch_url_exception(self):
        from app.services.check_service import CheckService

        with (
            patch(
                "app.services.check_service.CheckService._fetch_url_with_pyppeteer"
            ) as mock_pyppeteer,
            patch("requests.get") as mock_get,
        ):
            mock_pyppeteer.return_value = {"success": False, "error": "fail"}
            mock_get.side_effect = Exception("Network error")

            result = CheckService._fetch_url("https://example.com")

            assert result["success"] is False
