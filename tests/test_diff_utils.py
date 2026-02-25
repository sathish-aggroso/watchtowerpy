import pytest
from app.utils.diff_utils import (
    escape_html,
    compute_diff,
    extract_images,
    compute_image_diff,
)
from bs4 import BeautifulSoup


class TestDiffUtils:
    def test_escape_html(self):
        assert escape_html("&<>\"'") == "&amp;&lt;&gt;&quot;&#39;"
        assert escape_html("plain text") == "plain text"
        assert escape_html("") == ""

    def test_compute_diff_with_none_old_content(self):
        result = compute_diff(None, "new content")
        assert result is None

    def test_compute_diff_with_identical_content(self):
        result = compute_diff("same content", "same content")
        assert result is None

    def test_compute_diff_with_changes(self):
        old = "line 1\nline 2\nline 3"
        new = "line 1\nline 2 modified\nline 3"
        result = compute_diff(old, new)
        assert result is not None
        assert "---" in result
        assert "+++" in result

    def test_extract_images_with_src(self):
        html = '<html><body><img src="/image.png" alt="test"></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        images = extract_images(soup, "https://example.com")
        assert len(images) == 1
        assert images[0]["src"] == "https://example.com/image.png"
        assert images[0]["alt"] == "test"

    def test_extract_images_with_data_src(self):
        html = '<html><body><img data-src="/lazy.png"></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        images = extract_images(soup, "https://example.com")
        assert len(images) == 1

    def test_extract_images_no_images(self):
        html = "<html><body><p>No images</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        images = extract_images(soup, "https://example.com")
        assert len(images) == 0

    def test_compute_image_diff_no_url(self):
        result = compute_image_diff("<html></html>", "<html></html>", None)
        assert result == {"added": [], "removed": [], "changed": []}

    def test_compute_image_diff_with_added_images(self):
        old_html = "<html><body></body></html>"
        new_html = '<html><body><img src="/new.png"></body></html>'
        result = compute_image_diff(old_html, new_html, "https://example.com")
        assert len(result["added"]) == 1

    def test_compute_image_diff_with_removed_images(self):
        old_html = '<html><body><img src="/old.png"></body></html>'
        new_html = "<html><body></body></html>"
        result = compute_image_diff(old_html, new_html, "https://example.com")
        assert len(result["removed"]) == 1

    def test_compute_image_diff_with_changed_alt(self):
        old_html = '<html><body><img src="/img.png" alt="old"></body></html>'
        new_html = '<html><body><img src="/img.png" alt="new"></body></html>'
        result = compute_image_diff(old_html, new_html, "https://example.com")
        assert len(result["changed"]) == 1
