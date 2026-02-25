import hashlib
import difflib
import os
import subprocess
import sys
import tempfile
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

import requests
import aiohttp
import asyncio
from bs4 import BeautifulSoup


LLM_SUMMARY_COUNT = 0
LLM_SUMMARY_LIMIT = 5


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _highlight_html_tags(text: str) -> str:
    import re

    text = _escape_html(text)
    text = re.sub(
        r"(&lt;)(/?\w+)(.*?)(&gt;)",
        r'<span style="color: #9cdcfe">\1</span><span style="color: #4ec9b0">\2</span><span style="color: #d4d4d4">\3</span><span style="color: #9cdcfe">\4</span>',
        text,
    )
    text = re.sub(
        r"(&lt;!--.*?--&gt;)",
        r'<span style="color: #6a9955">\1</span>',
        text,
        flags=re.DOTALL,
    )
    return text


class CheckService:
    @staticmethod
    def check_link_async(link_id: int) -> Dict[str, Any]:
        from app.tasks.check_tasks import check_link_task

        logger.info(f"[check_link_async] Submitting task for link_id={link_id}")

        task = check_link_task.delay(link_id)

        return {
            "success": True,
            "task_id": task.id,
            "message": "Scraping started. Wait a few seconds for completion.",
        }

    @staticmethod
    def check_link(link_id: int) -> Dict[str, Any]:
        from app.repositories import (
            LinkRepository,
            InitialPageRepository,
            DiffRepository,
        )
        from flask import current_app

        logger.info(
            f"[check_link] Starting check for link_id={link_id}, take_screenshot={take_screenshot}"
        )

        link = LinkRepository.get_by_id(link_id)
        if not link:
            logger.warning(f"[check_link] Link not found: link_id={link_id}")
            return {"success": False, "error": "Link not found"}

        logger.info(f"[check_link] Fetching URL: {link['url']}")
        result = CheckService._fetch_url(link["url"])
        logger.debug(f"[check_link] Fetch result success={result.get('success')}")

        if result["success"]:
            content_hash = hashlib.md5(result["content"].encode()).hexdigest()

            initial_page = InitialPageRepository.get_by_link(link_id)
            latest_diff = DiffRepository.get_latest(link_id)

            previous_content = None
            if initial_page:
                previous_content = initial_page.get("full_content")
            elif latest_diff:
                previous_content = latest_diff.get("full_content")

            diff_content = (
                CheckService._compute_diff(previous_content, result["content"])
                if previous_content
                else None
            )

            summary = None
            try:
                global LLM_SUMMARY_COUNT, LLM_SUMMARY_LIMIT
                if diff_content:
                    if LLM_SUMMARY_COUNT >= LLM_SUMMARY_LIMIT:
                        remaining = max(0, LLM_SUMMARY_LIMIT - LLM_SUMMARY_COUNT)
                        summary = f"Free tier limit reached ({remaining} remaining). Subscribe for unlimited AI summaries."
                    else:
                        LLM_SUMMARY_COUNT += 1
                        summary = CheckService._generate_summary(
                            previous_content, result["content"], diff_content
                        )
                else:
                    summary = "No changes detected"
            except Exception as e:
                error_msg = str(e)
                if (
                    "500" in error_msg
                    or "insufficient balance" in error_msg.lower()
                    or "api_error" in error_msg
                ):
                    summary = "LLM API is limited (free tier - 5 summaries remaining)"
                else:
                    summary = f"Summary unavailable: {error_msg[:100]}"

            price_data = None
            try:
                price_data = CheckService._extract_price(result["content"])
            except Exception:
                pass

            screenshot_result = None
            screenshot_filename = None
            screenshot_dir = None
            temp_path = None
            diff_record = None

            if take_screenshot:
                logger.info(f"[check_link] Taking screenshot for {link['url']}")
                try:
                    screenshot_dir = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "static",
                        "screenshots",
                    )
                    os.makedirs(screenshot_dir, exist_ok=True)
                    temp_path = os.path.join(screenshot_dir, "temp_screenshot.png")
                    logger.debug(f"[check_link] Screenshot temp path: {temp_path}")
                    screenshot_result = CheckService._take_screenshot(
                        link["url"], temp_path
                    )
                    logger.debug(f"[check_link] Screenshot result: {screenshot_result}")
                except Exception as e:
                    logger.error(
                        f"[check_link] Screenshot error: {type(e).__name__}: {e}"
                    )

            diff_record = None

            if not initial_page:
                initial_record = InitialPageRepository.create(
                    link_id,
                    result["content"],
                    content_hash,
                    screenshot=None,
                )
                screenshot_filename = f"initial_{initial_record['id']}.png"
            else:
                previous_diff_id = latest_diff["id"] if latest_diff else None
                diff_record = DiffRepository.create(
                    link_id,
                    previous_diff_id,
                    result["content"],
                    content_hash,
                    diff_content,
                    summary,
                    price=price_data.get("text") if price_data else None,
                    price_amount=str(price_data.get("amount")) if price_data else None,
                    price_currency=price_data.get("currency") if price_data else None,
                    screenshot=None,
                    timezone="UTC",
                )
                screenshot_filename = f"diff_{diff_record['id']}.png"

            if screenshot_result and screenshot_dir and temp_path:
                try:
                    final_path = os.path.join(screenshot_dir, screenshot_filename)
                    if os.path.exists(temp_path):
                        os.rename(temp_path, final_path)
                        if not initial_page:
                            InitialPageRepository.update_screenshot(
                                link_id, screenshot_filename
                            )
                        else:
                            DiffRepository.update_screenshot(
                                diff_record["id"], screenshot_filename
                            )
                except Exception:
                    pass

            LinkRepository.update(
                link_id,
                last_checked=datetime.now().isoformat(),
                last_error=None,
            )

            logger.info(
                f"[check_link] Check completed for link_id={link_id}, success=True, has_changes={bool(diff_content)}"
            )
            return {
                "success": True,
                "summary": summary,
                "has_changes": bool(diff_content),
                "diff_id": diff_record.get("id") if diff_record else None,
                "is_initial": not initial_page,
                "price": price_data,
            }
        else:
            logger.warning(
                f"[check_link] Check failed for link_id={link_id}, error={result.get('error')}"
            )
            LinkRepository.update(link_id, last_error=result["error"])
            return {"success": False, "error": result["error"]}

    @staticmethod
    async def _fetch_url_async(url: str) -> Dict[str, Any]:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(
                timeout=timeout, headers=headers
            ) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    content = await response.text()
                    return {"success": True, "content": content[:500000]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _fetch_url(url: str) -> Dict[str, Any]:
        from app.tasks import fetch_url

        logger.info(f"[_fetch_url] Submitting celery task for {url}")
        task = fetch_url.delay(url)

        try:
            result = task.get(timeout=90)
            logger.info(
                f"[_fetch_url] Got result for {url}, success={result.get('success')}"
            )
            return result
        except Exception as e:
            logger.error(f"[_fetch_url] Celery task failed: {type(e).__name__}: {e}")
            pyppeteer_result = CheckService._fetch_url_with_pyppeteer(url)
            if pyppeteer_result.get("success"):
                return pyppeteer_result

            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                return {"success": True, "content": response.text[:500000]}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @staticmethod
    def _compute_diff(old_content: Optional[str], new_content: str) -> Optional[str]:
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

    @staticmethod
    def _compute_html_diff(
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
            return CheckService._text_diff_to_html(old_text, new_content, url)

        old_text = old_body.get_text(separator="\n", strip=True)
        new_text = new_body.get_text(separator="\n", strip=True)

        if old_text == new_text:
            return None

        css_content = ""
        if url:
            css_content = CheckService._download_css(url)

        diff_html = CheckService._generate_body_diff(old_body, new_body, css_content)
        return diff_html

    @staticmethod
    def _extract_images(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        from urllib.parse import urljoin

        images = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                img_url = urljoin(base_url, src)
                alt = img.get("alt", "")
                images.append({"src": img_url, "alt": alt})
        return images

    @staticmethod
    def _compute_image_diff(
        old_content: str, new_content: str, url: Optional[str]
    ) -> Dict[str, List]:
        from urllib.parse import urljoin

        result: Dict[str, List] = {"added": [], "removed": [], "changed": []}
        if not url:
            return result

        try:
            old_soup = BeautifulSoup(old_content, "html.parser")
            new_soup = BeautifulSoup(new_content, "html.parser")
        except Exception:
            return result

        old_images = CheckService._extract_images(old_soup, url)
        new_images = CheckService._extract_images(new_soup, url)

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

    @staticmethod
    def _generate_paragraph_diff(old_body, new_body, url: Optional[str]) -> str:
        from urllib.parse import urljoin

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

        old_images = CheckService._extract_images(old_body, url or "") if url else []
        new_images = CheckService._extract_images(new_body, url or "") if url else []

        img_added = [
            img
            for img in new_images
            if img["src"] not in {i["src"] for i in old_images}
        ]
        img_removed = [
            img
            for img in old_images
            if img["src"] not in {i["src"] for i in new_images}
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
                        f"<div class='diff-para'>{_escape_html(text[:200])}</div>"
                    )
            elif tag == "replace":
                for text in old_texts[i1:i2]:
                    html_parts.append(
                        f"<div class='diff-para diff-removed'>{_escape_html(text[:200])}</div>"
                    )
                for text in new_texts[j1:j2]:
                    html_parts.append(
                        f"<div class='diff-para diff-added'>{_escape_html(text[:200])}</div>"
                    )
            elif tag == "delete":
                for text in old_texts[i1:i2]:
                    html_parts.append(
                        f"<div class='diff-para diff-removed'>{_escape_html(text[:200])}</div>"
                    )
            elif tag == "insert":
                for text in new_texts[j1:j2]:
                    html_parts.append(
                        f"<div class='diff-para diff-added'>{_escape_html(text[:200])}</div>"
                    )

        html_parts.append("</body></html>")
        return "".join(html_parts)

    @staticmethod
    def _generate_code_diff(old_content: str, new_content: str) -> str:
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
                        f"<span style='flex: 1; padding: 0 12px; white-space: pre-wrap; word-break: break-all;'>{_highlight_html_tags(line)}</span></div>"
                    )
                    line_num += 1
            elif tag == "replace":
                for line in old_lines[i1:i2]:
                    html_parts.append(
                        f"<div style='display: flex; background: rgba(248, 81, 73, 0.15);'><span style='min-width: 50px; padding: 0 12px; text-align: right; color: #6e7681; background: #252526;'>-</span>"
                        f"<span style='flex: 1; padding: 0 12px; white-space: pre-wrap; word-break: break-all; color: #ffa198;'>{_highlight_html_tags(line)}</span></div>"
                    )
                for line in new_lines[j1:j2]:
                    html_parts.append(
                        f"<div style='display: flex; background: rgba(46, 160, 67, 0.15);'><span style='min-width: 50px; padding: 0 12px; text-align: right; color: #6e7681; background: #252526;'>+</span>"
                        f"<span style='flex: 1; padding: 0 12px; white-space: pre-wrap; word-break: break-all; color: #7ee787;'>{_highlight_html_tags(line)}</span></div>"
                    )
            elif tag == "delete":
                for line in old_lines[i1:i2]:
                    html_parts.append(
                        f"<div style='display: flex; background: rgba(248, 81, 73, 0.15);'><span style='min-width: 50px; padding: 0 12px; text-align: right; color: #6e7681; background: #252526;'>-</span>"
                        f"<span style='flex: 1; padding: 0 12px; white-space: pre-wrap; word-break: break-all; color: #ffa198;'>{_highlight_html_tags(line)}</span></div>"
                    )
            elif tag == "insert":
                for line in new_lines[j1:j2]:
                    html_parts.append(
                        f"<div style='display: flex; background: rgba(46, 160, 67, 0.15);'><span style='min-width: 50px; padding: 0 12px; text-align: right; color: #6e7681; background: #252526;'>+</span>"
                        f"<span style='flex: 1; padding: 0 12px; white-space: pre-wrap; word-break: break-all; color: #7ee787;'>{_highlight_html_tags(line)}</span></div>"
                    )

        html_parts.append("</div>")
        return "".join(html_parts)

    @staticmethod
    def _download_css(url: str) -> str:
        try:
            from urllib.parse import urljoin

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

    @staticmethod
    async def _take_screenshot_async(url: str, output_path: str) -> Optional[str]:
        import traceback

        try:
            from pyppeteer import launch

            logger.info(f"[screenshot] Starting screenshot for {url}")
            logger.debug(f"[screenshot] Output path: {output_path}")
            import os

            executable = os.environ.get("PYPPETEER_EXECUTABLE_PATH")

            browser = await launch(
                headless=True,
                executablePath=executable,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--proxy-bypass-list=*",
                ],
            )
            logger.debug("[screenshot] Browser launched")
            page = await browser.newPage()
            await page.setViewport({"width": 1920, "height": 1080})
            logger.debug(f"[screenshot] Navigating to {url}")
            response = await page.goto(
                url, {"waitUntil": "networkidle2", "timeout": 30000}
            )
            logger.debug(
                f"[screenshot] Page loaded, status: {response.status if response else 'None'}"
            )
            logger.info("[screenshot] Taking screenshot")
            await page.screenshot(path=output_path, fullPage=True)
            await browser.close()
            logger.info(f"[screenshot] Screenshot saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"[screenshot] Error: {type(e).__name__}: {e}")
            logger.debug(f"[screenshot] Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    def _take_screenshot(url: str, output_path: str) -> Optional[str]:
        from app.tasks import take_screenshot

        try:
            logger.info(f"[_take_screenshot] Submitting celery task for {url}")
            task = take_screenshot.delay(url, output_path)

            result = task.get(timeout=90)

            if result:
                logger.info(f"[_take_screenshot] Screenshot saved to {output_path}")
                return result
            else:
                logger.error(f"[_take_screenshot] Screenshot task returned None")
                return None
        except Exception as e:
            logger.error(
                f"[_take_screenshot] Celery task failed: {type(e).__name__}: {e}"
            )
            return None

    @staticmethod
    def _fetch_url_with_pyppeteer(url: str) -> Dict[str, Any]:
        import traceback

        try:
            logger.info(f"[playwright] Fetching URL: {url}")

            import asyncio
            import os
            from playwright.async_api import async_playwright

            async def fetch():
                executable = os.environ.get("PYPPETEER_EXECUTABLE_PATH")

                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        executable_path=executable,
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-gpu",
                            "--disable-cache",
                            "--disk-cache-size=0",
                            "--disable-web-security",
                            "--disable-features=IsolateOrigins,site-per-process",
                            "--allow-running-insecure-content",
                        ],
                    )
                    page = await browser.new_page(
                        viewport={"width": 1920, "height": 1080}
                    )
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(2)
                    html = await page.content()
                    await browser.close()
                    return html

            content = asyncio.run(fetch())
            logger.info(
                f"[playwright] Successfully fetched {url}, content length: {len(content)}"
            )
            return {"success": True, "content": content[:500000]}

        except Exception as e:
            logger.error(f"[playwright] Error fetching {url}: {type(e).__name__}: {e}")
            logger.debug(f"[playwright] Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _extract_price(content: str) -> Optional[Dict[str, Any]]:
        try:
            from price_parser import Price
            import re

            price_patterns = [
                r"\$\s?[\d,]+\.?\d*",
                r"USD\s?[\d,]+\.?\d*",
                r"€\s?[\d,]+\.?\d*",
                r"£\s?[\d,]+\.?\d*",
                r"₹\s?[\d,]+\.?\d*",
                r"[\d,]+\.?\d*\s?(?:USD|EUR|GBP|INR|CAD|AUD)",
                r'data-price="(\d+)"',
            ]

            prices_found = []
            for pattern in price_patterns:
                matches = re.findall(pattern, content[:10000])
                prices_found.extend(matches)

            if not prices_found:
                return None

            latest_price = prices_found[-1]
            try:
                parsed = Price.fromstring(
                    f"${latest_price}" if latest_price.isdigit() else latest_price
                )
                return {
                    "amount": float(latest_price) if latest_price.isdigit() else None,
                    "currency": "$",
                    "text": f"${latest_price}",
                }
            except:
                return {
                    "raw": latest_price,
                    "text": latest_price,
                }
        except Exception:
            return None

    @staticmethod
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
                    html_parts.append(
                        f"<div class='diff-line'>{_escape_html(line)}</div>"
                    )
            elif tag == "replace":
                for line in old_lines[i1:i2]:
                    html_parts.append(
                        f"<div class='diff-removed'>{_escape_html(line)}</div>"
                    )
                for line in new_lines[j1:j2]:
                    html_parts.append(
                        f"<div class='diff-added'>{_escape_html(line)}</div>"
                    )
            elif tag == "delete":
                for line in old_lines[i1:i2]:
                    html_parts.append(
                        f"<div class='diff-removed'>{_escape_html(line)}</div>"
                    )
            elif tag == "insert":
                for line in new_lines[j1:j2]:
                    html_parts.append(
                        f"<div class='diff-added'>{_escape_html(line)}</div>"
                    )

        html_parts.append("</body></html>")
        return "".join(html_parts)

    @staticmethod
    def _text_diff_to_html(
        old_text: str, new_content: str, url: Optional[str] = None
    ) -> str:
        old_lines = old_text.splitlines()
        new_lines = new_content.splitlines()

        css_content = ""
        if url:
            css_content = CheckService._download_css(url)

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
                            f"<div class='diff-unchanged'>{_escape_html(line)}</div>"
                        )
            elif tag == "replace":
                for line in old_lines[i1:i2]:
                    if line.strip():
                        html_parts.append(
                            f"<div class='diff-removed'>{_escape_html(line)}</div>"
                        )
                for line in new_lines[j1:j2]:
                    if line.strip():
                        html_parts.append(
                            f"<div class='diff-added'>{_escape_html(line)}</div>"
                        )
            elif tag == "delete":
                for line in old_lines[i1:i2]:
                    if line.strip():
                        html_parts.append(
                            f"<div class='diff-removed'>{_escape_html(line)}</div>"
                        )
            elif tag == "insert":
                for line in new_lines[j1:j2]:
                    if line.strip():
                        html_parts.append(
                            f"<div class='diff-added'>{_escape_html(line)}</div>"
                        )

        html_parts.append("</div></body></html>")
        return "".join(html_parts)

    @staticmethod
    def _generate_summary(
        old_content: Optional[str], new_content: str, diff_text: str
    ) -> str:
        from dotenv import load_dotenv

        load_dotenv()

        import os

        llm_api_key = os.environ.get("CEREBRAS_API_KEY", "") or os.environ.get(
            "LLM_API_KEY", ""
        )

        if not llm_api_key:
            try:
                from flask import current_app

                llm_api_key = current_app.config.get("LLM_API_KEY", "")
            except RuntimeError:
                pass

        if not llm_api_key:
            return CheckService._generate_summary_simple(diff_text)

        llm_model = os.environ.get("LLM_MODEL", "llama3.1-8b")
        llm_provider = os.environ.get("LLM_PROVIDER", "cerebras")

        try:
            from flask import current_app

            llm_model = current_app.config.get("LLM_MODEL", llm_model)
            llm_provider = current_app.config.get("LLM_PROVIDER", llm_provider)
        except RuntimeError:
            pass

        if not llm_api_key:
            return CheckService._generate_summary_simple(diff_text)

        llm_model = os.environ.get("LLM_MODEL", "llama3.1-8b")
        llm_provider = os.environ.get("LLM_PROVIDER", "cerebras")

        try:
            from flask import current_app

            llm_model = current_app.config.get("LLM_MODEL", llm_model)
            llm_provider = current_app.config.get("LLM_PROVIDER", llm_provider)
        except RuntimeError:
            pass

        llm_model = os.environ.get("LLM_MODEL", "gemma-3-27b-it")
        llm_provider = os.environ.get("LLM_PROVIDER", "gemini")

        try:
            from flask import current_app

            llm_model = current_app.config.get("LLM_MODEL", llm_model)
            llm_provider = current_app.config.get("LLM_PROVIDER", llm_provider)
        except RuntimeError:
            pass

        if not llm_api_key:
            return CheckService._generate_summary_simple(diff_text)

        old_preview = (
            (old_content[:2000] + "...")
            if old_content and len(old_content) > 2000
            else (old_content or "No previous content")
        )
        new_preview = (
            (new_content[:2000] + "...") if len(new_content) > 2000 else new_content
        )

        prompt = f"""You are analyzing website changes. Compare the PREVIOUS version and CURRENT version of a webpage, then summarize what changed in 2-3 sentences. Include specific HTML snippets or elements as proof of the changes. Format your response in markdown.

PREVIOUS VERSION:
{old_preview}

CURRENT VERSION:
{new_preview}

DIFF (for reference):
{diff_text[:3000]}

Summary of changes with proof (in markdown):"""

        try:
            import asyncio
            import os
            from cerebras.cloud.sdk import AsyncCerebras

            for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
                os.environ.pop(key, None)
                os.environ.pop(key.lower(), None)

            client = AsyncCerebras(api_key=llm_api_key)

            async def main():
                chat_completion = await client.chat.completions.create(
                    model="llama3.1-8b",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                )
                return chat_completion.choices[0].message.content

            result = asyncio.run(main())
            return result.strip() if result else ""
        except Exception as e:
            raise Exception(f"LLM error: {e}")

    @staticmethod
    def _generate_summary_simple(diff_text: str) -> str:
        if not diff_text:
            return "No changes detected"

        changes = []
        for line in diff_text.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                changes.append(f"Added: {line[1:].strip()[:100]}")
            elif line.startswith("-") and not line.startswith("---"):
                changes.append(f"Removed: {line[1:].strip()[:100]}")

        if changes:
            return "; ".join(changes[:3])
        return "Content changed"
