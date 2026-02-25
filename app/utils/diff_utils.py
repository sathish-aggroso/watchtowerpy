import difflib
from typing import Optional, Dict, List, Any


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def compute_diff(old_content: Optional[str], new_content: str) -> Optional[str]:
    if not old_content:
        return None

    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="previous",
            tofile="current",
            lineterm="",
            n=3,
        )
    )

    return "".join(diff) if diff else None


def extract_images(soup, base_url: str) -> List[Dict[str, str]]:
    from urllib.parse import urljoin

    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src:
            img_url = urljoin(base_url, src)
            alt = img.get("alt", "")
            images.append({"src": img_url, "alt": alt})
    return images


def compute_image_diff(
    old_content: str, new_content: str, url: Optional[str]
) -> Dict[str, List]:
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    result: Dict[str, List] = {"added": [], "removed": [], "changed": []}
    if not url:
        return result

    try:
        old_soup = BeautifulSoup(old_content, "html.parser")
        new_soup = BeautifulSoup(new_content, "html.parser")
    except Exception:
        return result

    old_images = extract_images(old_soup, url)
    new_images = extract_images(new_soup, url)

    old_srcs = {img["src"] for img in old_images}
    new_srcs = {img["src"] for img in new_images}

    for img in new_images:
        if img["src"] not in old_srcs:
            result["added"].append(img)
        else:
            old_img = next((i for i in old_images if i["src"] == img["src"]), None)
            if old_img and old_img.get("alt") != img.get("alt"):
                result["changed"].append({"old": old_img, "new": img})

    for img in old_images:
        if img["src"] not in new_srcs:
            result["removed"].append(img)

    return result
