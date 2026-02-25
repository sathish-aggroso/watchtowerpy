import pytest
from unittest.mock import MagicMock, patch


class TestHtmlDiffUtils:
    def test_compute_html_diff_none_old(self):
        from app.utils.html_diff_utils import compute_html_diff

        result = compute_html_diff(None, "new content")

        assert result is None

    def test_compute_html_diff_none_new(self):
        from app.utils.html_diff_utils import compute_html_diff

        result = compute_html_diff("old content", None)

        assert result is None

    def test_compute_html_diff_same(self):
        from app.utils.html_diff_utils import compute_html_diff

        content = "<html><body><p>Same</p></body></html>"
        result = compute_html_diff(content, content)

        assert result is None

    def test_compute_html_diff_with_body(self):
        from app.utils.html_diff_utils import compute_html_diff

        old = "<html><body><p>Old</p></body></html>"
        new = "<html><body><p>New</p></body></html>"

        result = compute_html_diff(old, new)

        assert result is not None

    def test_compute_html_diff_no_body_same_text(self):
        from app.utils.html_diff_utils import compute_html_diff

        old = "<html><head><title>Test</title></head></html>"
        new = "<html><head><title>Test</title></head></html>"

        result = compute_html_diff(old, new)

        assert result is None

    def test_compute_html_diff_no_body_diff_text(self):
        from app.utils.html_diff_utils import compute_html_diff

        old = "<html><head><title>Old</title></head></html>"
        new = "<html><head><title>New</title></head></html>"

        result = compute_html_diff(old, new)

        assert result is not None
        assert "<!DOCTYPE html>" in result

    def test_compute_html_diff_invalid(self):
        from app.utils.html_diff_utils import compute_html_diff

        result = compute_html_diff("invalid", "content")

        assert result is not None

    def test_compute_html_diff_with_url(self):
        from app.utils.html_diff_utils import compute_html_diff

        old = "<html><body><p>Old</p></body></html>"
        new = "<html><body><p>New</p></body></html>"

        with patch("app.utils.html_diff_utils._download_css") as mock_download:
            mock_download.return_value = ""
            result = compute_html_diff(old, new, "https://example.com")

            assert result is not None
            mock_download.assert_called_once()

    def test_generate_paragraph_diff(self):
        from app.utils.html_diff_utils import generate_paragraph_diff
        from bs4 import BeautifulSoup

        old_soup = BeautifulSoup("<body><p>Old</p></body>", "html.parser")
        new_soup = BeautifulSoup("<body><p>New</p></body>", "html.parser")

        old_body = old_soup.find("body")
        new_body = new_soup.find("body")

        result = generate_paragraph_diff(old_body, new_body, None)

        assert result is not None

    def test_generate_paragraph_diff_with_images(self):
        from app.utils.html_diff_utils import generate_paragraph_diff
        from bs4 import BeautifulSoup

        old_soup = BeautifulSoup(
            '<body><p>Text</p><img src="/old.png"></body>', "html.parser"
        )
        new_soup = BeautifulSoup(
            '<body><p>Text</p><img src="/new.png"></body>', "html.parser"
        )

        old_body = old_soup.find("body")
        new_body = new_soup.find("body")

        result = generate_paragraph_diff(old_body, new_body, "https://example.com")

        assert result is not None

    def test_generate_paragraph_diff_empty(self):
        from app.utils.html_diff_utils import generate_paragraph_diff
        from bs4 import BeautifulSoup

        old_soup = BeautifulSoup("<body></body>", "html.parser")
        new_soup = BeautifulSoup("<body></body>", "html.parser")

        old_body = old_soup.find("body")
        new_body = new_soup.find("body")

        result = generate_paragraph_diff(old_body, new_body, None)

        assert result is not None

    def test_generate_code_diff(self):
        from app.utils.html_diff_utils import generate_code_diff

        old_content = "<html><body><p>Old</p></body></html>"
        new_content = "<html><body><p>New</p></body></html>"

        result = generate_code_diff(old_content, new_content)

        assert result is not None

    def test_generate_code_diff_no_body(self):
        from app.utils.html_diff_utils import generate_code_diff

        old_content = "<html><head><title>Test</title></head></html>"
        new_content = "<html><head><title>Test</title></head></html>"

        result = generate_code_diff(old_content, new_content)

        assert result is not None

    def test_generate_code_diff_empty_body(self):
        from app.utils.html_diff_utils import generate_code_diff

        old_content = "<html><body></body></html>"
        new_content = "<html><body></body></html>"

        result = generate_code_diff(old_content, new_content)

        assert result is not None

    def test_download_css_exception(self):
        from app.utils.html_diff_utils import _download_css

        with patch("requests.Request") as mock_request:
            mock_request.side_effect = Exception("Network error")
            result = _download_css("https://example.com")

            assert result == ""

    def test_download_css_bad_response(self):
        from app.utils.html_diff_utils import _download_css

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.ok = False
            mock_get.return_value = mock_response

            result = _download_css("https://example.com")

            assert result == ""


class TestDiffUtils:
    def test_escape_html(self):
        from app.utils.diff_utils import escape_html

        result = escape_html("<>&'\"")

        assert "&lt;" in result
        assert "&gt;" in result

    def test_extract_images(self):
        from app.utils.diff_utils import extract_images
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<body><img src="/image.png" alt="test"></body>', "html.parser"
        )
        body = soup.find("body")

        result = extract_images(body, "https://example.com")

        assert len(result) >= 1

    def test_extract_images_no_body(self):
        from app.utils.diff_utils import extract_images
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<html></html>", "html.parser")

        result = extract_images(soup, "https://example.com")

        assert result == []
