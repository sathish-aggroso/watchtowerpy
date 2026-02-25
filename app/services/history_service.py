from typing import List, Dict, Any, Optional

from app.repositories import HistoryRepository, LinkRepository


class HistoryService:
    @staticmethod
    def get_link_history(link_id: int) -> List[Dict[str, Any]]:
        return HistoryRepository.get_by_link(link_id, limit=5)

    @staticmethod
    def get_history(history_id: int) -> Optional[Dict[str, Any]]:
        from app.services.check_service import CheckService

        history = HistoryRepository.get_by_id(history_id)
        if not history:
            return None

        link = LinkRepository.get_by_id(history["link_id"])

        is_initial = HistoryRepository.is_initial_entry(history["link_id"], history_id)

        if is_initial:
            return {
                "entry": history,
                "link": link,
                "diff": None,
                "previous": None,
                "html_diff": None,
                "paragraph_diff": None,
                "code_diff": None,
                "image_diff": None,
                "current_screenshot": history.get("screenshot"),
                "previous_screenshot": None,
                "is_initial": True,
            }

        prev = HistoryRepository.get_previous(history["link_id"], history_id)

        diff = (
            CheckService._compute_diff(prev["content"], history["content"])
            if prev
            else None
        )

        html_diff = None
        paragraph_diff = None
        code_diff = None
        image_diff = None

        if prev and history.get("content") and link:
            url = link.get("url")
            html_diff = CheckService._compute_html_diff(
                prev["content"], history["content"], url
            )
            from bs4 import BeautifulSoup

            old_soup = BeautifulSoup(prev["content"], "html.parser")
            new_soup = BeautifulSoup(history["content"], "html.parser")
            old_body = old_soup.find("body")
            new_body = new_soup.find("body")
            if old_body and new_body:
                old_text = old_body.get_text(strip=True)
                new_text = new_body.get_text(strip=True)
                if old_text:
                    change_percent = (
                        abs(len(new_text) - len(old_text)) / len(old_text)
                    ) * 100
                    history["change_percent"] = min(change_percent, 100)
                paragraph_diff = CheckService._generate_paragraph_diff(
                    new_body, old_body, url
                )
                code_diff = CheckService._generate_code_diff(
                    history["content"], prev["content"]
                )
            image_diff = CheckService._compute_image_diff(
                prev["content"], history["content"], url
            )

        return {
            "entry": history,
            "link": link,
            "diff": diff,
            "previous": prev,
            "html_diff": html_diff,
            "paragraph_diff": paragraph_diff,
            "code_diff": code_diff,
            "image_diff": image_diff,
            "current_screenshot": history.get("screenshot"),
            "previous_screenshot": prev.get("screenshot") if prev else None,
            "is_initial": False,
        }
