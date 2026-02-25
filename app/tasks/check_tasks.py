import os
import hashlib
import difflib
import logging

from datetime import datetime
from typing import Optional, Dict, Any

import requests

from bs4 import BeautifulSoup

from app.celery_config import celery_app
from app.tasks.screenshot_tasks import fetch_url_sync

logger = logging.getLogger(__name__)


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


class CheckServiceCelery:
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

    @staticmethod
    def _update_link_and_create_records(
        link_id: int,
        content: str,
        content_hash: str,
        summary: str = None,
        price_data: Dict = None,
    ) -> Dict[str, Any]:
        from app.repositories import (
            LinkRepository,
            InitialPageRepository,
            DiffRepository,
        )

        initial_page = InitialPageRepository.get_by_link(link_id)
        latest_diff = DiffRepository.get_latest(link_id)

        previous_content = None
        if initial_page:
            previous_content = initial_page.get("full_content")
        elif latest_diff:
            previous_content = latest_diff.get("full_content")

        diff_content = (
            CheckServiceCelery._compute_diff(previous_content, content)
            if previous_content
            else None
        )

        diff_record = None

        if not initial_page:
            initial_record = InitialPageRepository.create(
                link_id,
                content,
                content_hash,
            )
        else:
            previous_diff_id = latest_diff["id"] if latest_diff else None
            diff_record = DiffRepository.create(
                link_id,
                previous_diff_id,
                content,
                content_hash,
                diff_content,
                summary,
                price=price_data.get("text") if price_data else None,
                price_amount=str(price_data.get("amount")) if price_data else None,
                price_currency=price_data.get("currency") if price_data else None,
                timezone="UTC",
            )

        LinkRepository.update(
            link_id,
            last_checked=datetime.now().isoformat(),
            last_error=None,
        )

        return {
            "success": True,
            "summary": summary,
            "has_changes": bool(diff_content),
            "diff_id": diff_record.get("id") if diff_record else None,
            "is_initial": not initial_page,
            "price": price_data,
        }


@celery_app.task(bind=True, name="app.tasks.check_link")
def check_link_task(self, link_id: int):
    from app.repositories import (
        LinkRepository,
        InitialPageRepository,
        DiffRepository,
    )

    logger.info(f"[check_link] Starting check for link_id={link_id}")

    link = LinkRepository.get_by_id(link_id)
    if not link:
        logger.warning(f"[check_link] Link not found: link_id={link_id}")
        return {"success": False, "error": "Link not found"}

    logger.info(f"[check_link] Fetching URL: {link['url']}")

    fetch_result = fetch_url_sync(link["url"])
    logger.debug(f"[check_link] Fetch result success={fetch_result.get('success')}")

    if fetch_result["success"]:
        content = fetch_result["content"]
        content_hash = hashlib.md5(content.encode()).hexdigest()

        initial_page = InitialPageRepository.get_by_link(link_id)
        latest_diff = DiffRepository.get_latest(link_id)

        previous_content = None
        if initial_page:
            previous_content = initial_page.get("full_content")
        elif latest_diff:
            previous_content = latest_diff.get("full_content")

        diff_content = (
            CheckServiceCelery._compute_diff(previous_content, content)
            if previous_content
            else None
        )

        price_data = None
        try:
            price_data = CheckServiceCelery._extract_price(content)
        except Exception:
            pass

        previous_content_for_summary = previous_content if previous_content else None
        summary = "Processing complete"
        if previous_content_for_summary:
            try:
                from app.services.check_service import CheckService

                summary = CheckService._generate_summary(
                    previous_content_for_summary, content, diff_content
                )
            except Exception as e:
                logger.warning(f"[check_link] LLM summary failed: {e}")
                summary = CheckServiceCelery._generate_summary_simple(diff_content)

        result = CheckServiceCelery._update_link_and_create_records(
            link_id,
            content,
            content_hash,
            summary=summary,
            price_data=price_data,
        )

        logger.info(f"[check_link] Check completed for link_id={link_id}, success=True")
        return result
    else:
        LinkRepository.update(link_id, last_error=fetch_result["error"])
        logger.warning(
            f"[check_link] Check failed for link_id={link_id}, error={fetch_result.get('error')}"
        )
        return {"success": False, "error": fetch_result["error"]}
