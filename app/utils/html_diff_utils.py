import difflib
from typing import Optional
from bs4 import BeautifulSoup

from app.utils.diff_utils import escape_html, extract_images


def compute_html_diff(
    old_content: Optional[str], new_content: str, url: Optional[str] = None
) -> Optional[str]:
    if not old_content or not new_content:
        return None

    try:
        old_soup = BeautifulSoup(old_content, "html.parser")
        new_soup = BeautifulSoup(new_content, "html.parser")
    except Exception:
        return None

    old_body = old_soup.find("body")
    new_body = new_soup.find("body")

    if not old_body or not new_body:
        old_text = old_soup.get_text(separator=" ", strip=True)
        new_text = new_soup.get_text(separator=" ", strip=True)
        if old_text == new_text:
            return None
        return _text_diff_to_html(old_text, new_content, url)

    old_text = old_body.get_text(separator="\n", strip=True)
    new_text = new_body.get_text(separator="\n", strip=True)

    if old_text == new_text:
        return None

    css_content = ""
    if url:
        css_content = _download_css(url)

    diff_html = _generate_body_diff(old_body, new_body, css_content)
    return diff_html


def _download_css(url: str) -> str:
    import requests
    from urllib.parse import urljoin

    try:
        parsed_url = requests.Request("GET", url).prepare()
        base_url = parsed_url.url

        response = requests.get(
            base_url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        if not response.ok:
            return ""

        soup = BeautifulSoup(response.text, "html.parser")
        css_links = soup.find_all("link", rel="stylesheet")

        all_css = []
        for link in css_links:
            href = link.get("href")
            if href:
                css_url = urljoin(base_url, href)
                try:
                    css_response = requests.get(
                        css_url, timeout=5, headers={"User-Agent": "Mozilla/5.0"}
                    )
                    if css_response.ok:
                        all_css.append(css_response.text)
                except Exception:
                    pass

        return "\n".join(all_css)
    except Exception:
        return ""


def _generate_body_diff(old_body, new_body, css_content: str) -> str:
    old_text = old_body.get_text(separator="\n", strip=True)
    new_text = new_body.get_text(separator="\n", strip=True)

    old_lines = [l for l in old_text.splitlines() if l.strip()]
    new_lines = [l for l in new_text.splitlines() if l.strip()]

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    custom_css = (
        """
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6; 
            padding: 20px; 
            max-width: 1200px; 
            margin: 0 auto;
            background: #fff;
            color: #333;
        }
        .diff-added { 
            background: #90EE90; 
            color: #006400;
            padding: 2px 4px;
            border-radius: 2px;
        }
        .diff-removed {
            background: #FFB6C1;
            color: #8B0000;
            padding: 2px 4px;
            border-radius: 2px;
            text-decoration: line-through;
        }
        .diff-line {
            padding: 4px 8px;
            margin: 2px 0;
            border-radius: 3px;
        }
        h1, h2, h3, h4, h5, h6 { margin-top: 1em; margin-bottom: 0.5em; }
        p { margin: 0.5em 0; }
        a { color: #0066cc; }
        img { max-width: 100%; height: auto; }
    """
        + css_content
    )

    html_parts = [
        "<!DOCTYPE html>",
        "<html><head>",
        "<meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<style>{custom_css}</style>",
        "</head><body>",
    ]

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for line in old_lines[i1:i2]:
                html_parts.append(f"<div class='diff-line'>{escape_html(line)}</div>")
        elif tag == "replace":
            for line in old_lines[i1:i2]:
                html_parts.append(
                    f"<div class='diff-removed'>{escape_html(line)}</div>"
                )
            for line in new_lines[j1:j2]:
                html_parts.append(f"<div class='diff-added'>{escape_html(line)}</div>")
        elif tag == "delete":
            for line in old_lines[i1:i2]:
                html_parts.append(
                    f"<div class='diff-removed'>{escape_html(line)}</div>"
                )
        elif tag == "insert":
            for line in new_lines[j1:j2]:
                html_parts.append(f"<div class='diff-added'>{escape_html(line)}</div>")

    html_parts.append("</body></html>")
    return "".join(html_parts)


def _text_diff_to_html(
    old_text: str, new_content: str, url: Optional[str] = None
) -> str:
    new_lines = new_content.splitlines()

    css_content = ""
    if url:
        css_content = _download_css(url)

    custom_css = (
        """
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; 
            padding: 20px; 
            max-width: 1200px; 
            margin: 0 auto;
            background: #fff;
            color: #333;
        }
        .diff-added { 
            background: #90EE90; 
            color: #006400;
            padding: 2px 4px;
            border-radius: 2px;
        }
        .diff-removed {
            background: #FFB6C1;
            color: #8B0000;
            padding: 2px 4px;
            border-radius: 2px;
            text-decoration: line-through;
        }
        .diff-line, .diff-unchanged {
            padding: 4px 8px;
            margin: 2px 0;
            border-radius: 3px;
        }
    """
        + css_content
    )

    old_lines = old_text.splitlines()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    html_parts = [
        "<!DOCTYPE html>",
        "<html><head>",
        "<meta charset='utf-8'>",
        f"<style>{custom_css}</style>",
        "</head><body><div class='diff-container'>",
    ]

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for line in old_lines[i1:i2]:
                if line.strip():
                    html_parts.append(
                        f"<div class='diff-unchanged'>{escape_html(line)}</div>"
                    )
        elif tag == "replace":
            for line in old_lines[i1:i2]:
                if line.strip():
                    html_parts.append(
                        f"<div class='diff-removed'>{escape_html(line)}</div>"
                    )
            for line in new_lines[j1:j2]:
                if line.strip():
                    html_parts.append(
                        f"<div class='diff-added'>{escape_html(line)}</div>"
                    )
        elif tag == "delete":
            for line in old_lines[i1:i2]:
                if line.strip():
                    html_parts.append(
                        f"<div class='diff-removed'>{escape_html(line)}</div>"
                    )
        elif tag == "insert":
            for line in new_lines[j1:j2]:
                if line.strip():
                    html_parts.append(
                        f"<div class='diff-added'>{escape_html(line)}</div>"
                    )

    html_parts.append("</div></body></html>")
    return "".join(html_parts)


def generate_paragraph_diff(old_body, new_body, url: Optional[str]) -> str:
    old_paragraphs = old_body.find_all(
        ["p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "span"]
    )
    new_paragraphs = new_body.find_all(
        ["p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "span"]
    )

    old_texts = [
        p.get_text(strip=True) for p in old_paragraphs if p.get_text(strip=True)
    ]
    new_texts = [
        p.get_text(strip=True) for p in new_paragraphs if p.get_text(strip=True)
    ]

    matcher = difflib.SequenceMatcher(None, old_texts, new_texts)

    html_parts = [
        "<!DOCTYPE html>",
        "<html><head>",
        "<meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<style>",
        """
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               line-height: 1.7; padding: 20px; max-width: 900px; margin: 0 auto; background: #fafafa; color: #333; }
        .diff-para { padding: 12px 16px; margin: 8px 0; border-radius: 8px; background: #fff; 
                     border: 1px solid #e5e7eb; }
        .diff-added { background: #dcfce7; border-color: #86efac; }
        .diff-removed { background: #fee2e2; border-color: #fca5a5; text-decoration: line-through; opacity: 0.7; }
        .diff-img { max-width: 200px; max-height: 150px; border-radius: 8px; margin: 8px 4px; border: 2px solid #e5e7eb; }
        .diff-img-added { border-color: #22c55e; }
        .diff-img-removed { border-color: #ef4444; opacity: 0.6; }
        .img-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
        h1, h2, h3 { margin: 16px 0 8px; }
        """,
        "</style></head><body>",
    ]

    old_images = extract_images(old_body, url or "") if url else []
    new_images = extract_images(new_body, url or "") if url else []

    img_added = [
        img for img in new_images if img["src"] not in {i["src"] for i in old_images}
    ]
    img_removed = [
        img for img in old_images if img["src"] not in {i["src"] for i in new_images}
    ]

    if img_added or img_removed:
        html_parts.append(
            "<div class='diff-para'><strong>Images Changed</strong><div class='img-row'>"
        )
        for img in img_removed:
            html_parts.append(
                f"<img class='diff-img diff-img-removed' src='{img['src']}' alt='{img['alt']}' title='Removed'>"
            )
        for img in img_added:
            html_parts.append(
                f"<img class='diff-img diff-img-added' src='{img['src']}' alt='{img['alt']}' title='Added'>"
            )
        html_parts.append("</div></div>")

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for text in old_texts[i1:i2][:3]:
                html_parts.append(
                    f"<div class='diff-para'>{escape_html(text[:200])}</div>"
                )
        elif tag == "replace":
            for text in old_texts[i1:i2]:
                html_parts.append(
                    f"<div class='diff-para diff-removed'>{escape_html(text[:200])}</div>"
                )
            for text in new_texts[j1:j2]:
                html_parts.append(
                    f"<div class='diff-para diff-added'>{escape_html(text[:200])}</div>"
                )
        elif tag == "delete":
            for text in old_texts[i1:i2]:
                html_parts.append(
                    f"<div class='diff-para diff-removed'>{escape_html(text[:200])}</div>"
                )
        elif tag == "insert":
            for text in new_texts[j1:j2]:
                html_parts.append(
                    f"<div class='diff-para diff-added'>{escape_html(text[:200])}</div>"
                )

    html_parts.append("</body></html>")
    return "".join(html_parts)


def generate_code_diff(old_content: str, new_content: str) -> str:
    old_soup = BeautifulSoup(old_content, "html.parser")
    new_soup = BeautifulSoup(new_content, "html.parser")

    old_body = old_soup.find("body")
    new_body = new_soup.find("body")

    old_html = old_body.prettify() if old_body else ""
    new_html = new_body.prettify() if new_body else ""

    old_lines = old_html.splitlines()
    new_lines = new_html.splitlines()

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    html_parts = [
        "<div style='background: #1e1e1e; color: #d4d4d4; font-family: Consolas, Monaco, monospace; font-size: 14px; line-height: 1.5; padding: 16px; margin: 0;'>",
    ]

    line_num = 1
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for idx, line in enumerate(old_lines[i1:i2]):
                html_parts.append(
                    f"<div style='display: flex;'><span style='min-width: 50px; padding: 0 12px; text-align: right; color: #6e7681; background: #252526; user-select: none;'>{line_num}</span>"
                    f"<span style='flex: 1; padding: 0 12px; white-space: pre-wrap; word-break: break-all;'>{escape_html(line)}</span></div>"
                )
                line_num += 1
        elif tag == "replace":
            for line in old_lines[i1:i2]:
                html_parts.append(
                    f"<div style='display: flex; background: rgba(248, 81, 73, 0.15);'><span style='min-width: 50px; padding: 0 12px; text-align: right; color: #6e7681; background: #252526;'>-</span>"
                    f"<span style='flex: 1; padding: 0 12px; white-space: pre-wrap; word-break: break-all; color: #ffa198;'>{escape_html(line)}</span></div>"
                )
            for line in new_lines[j1:j2]:
                html_parts.append(
                    f"<div style='display: flex; background: rgba(46, 160, 67, 0.15);'><span style='min-width: 50px; padding: 0 12px; text-align: right; color: #6e7681; background: #252526;'>+</span>"
                    f"<span style='flex: 1; padding: 0 12px; white-space: pre-wrap; word-break: break-all; color: #7ee787;'>{escape_html(line)}</span></div>"
                )
        elif tag == "delete":
            for line in old_lines[i1:i2]:
                html_parts.append(
                    f"<div style='display: flex; background: rgba(248, 81, 73, 0.15);'><span style='min-width: 50px; padding: 0 12px; text-align: right; color: #6e7681; background: #252526;'>-</span>"
                    f"<span style='flex: 1; padding: 0 12px; white-space: pre-wrap; word-break: break-all; color: #ffa198;'>{escape_html(line)}</span></div>"
                )
        elif tag == "insert":
            for line in new_lines[j1:j2]:
                html_parts.append(
                    f"<div style='display: flex; background: rgba(46, 160, 67, 0.15);'><span style='min-width: 50px; padding: 0 12px; text-align: right; color: #6e7681; background: #252526;'>+</span>"
                    f"<span style='flex: 1; padding: 0 12px; white-space: pre-wrap; word-break: break-all; color: #7ee787;'>{escape_html(line)}</span></div>"
                )

    html_parts.append("</div>")
    return "".join(html_parts)
