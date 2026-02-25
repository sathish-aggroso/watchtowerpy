import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models import History
from app.extensions import get_session


class HistoryRepository:
    @staticmethod
    def get_by_link(link_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        session = get_session()
        try:
            history = (
                session.query(History)
                .filter_by(link_id=link_id)
                .order_by(History.checked_at.desc())
                .limit(limit)
                .all()
            )
            return [h.to_dict() for h in history]
        finally:
            session.close()

    @staticmethod
    def get_oldest(link_id: int) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            history = (
                session.query(History)
                .filter_by(link_id=link_id)
                .order_by(History.checked_at.asc())
                .first()
            )
            return history.to_dict() if history else None
        finally:
            session.close()

    @staticmethod
    def get_by_id(history_id: int) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            history = session.query(History).filter_by(id=history_id).first()
            return history.to_dict() if history else None
        finally:
            session.close()

    @staticmethod
    def get_previous(link_id: int, history_id: int) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            prev = (
                session.query(History)
                .filter(History.link_id == link_id, History.id < history_id)
                .order_by(History.id.desc())
                .first()
            )
            return prev.to_dict() if prev else None
        finally:
            session.close()

    @staticmethod
    def get_baseline(link_id: int) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            baseline = (
                session.query(History)
                .filter_by(link_id=link_id)
                .order_by(History.checked_at.asc())
                .first()
            )
            return baseline.to_dict() if baseline else None
        finally:
            session.close()

    @staticmethod
    def is_initial_entry(link_id: int, history_id: int) -> bool:
        session = get_session()
        try:
            first_entry = (
                session.query(History)
                .filter_by(link_id=link_id)
                .order_by(History.checked_at.asc())
                .first()
            )
            return first_entry and first_entry.id == history_id
        finally:
            session.close()

    @staticmethod
    def create(
        link_id: int,
        content: str,
        content_hash: str,
        summary: Optional[str] = None,
        price: Optional[str] = None,
        price_amount: Optional[str] = None,
        price_currency: Optional[str] = None,
        screenshot: Optional[str] = None,
        timezone: str = "UTC",
    ) -> Dict[str, Any]:
        session = get_session()
        try:
            history = History(
                link_id=link_id,
                content=content,
                content_hash=content_hash,
                summary=summary,
                price=price,
                price_amount=price_amount,
                price_currency=price_currency,
                screenshot=screenshot,
                timezone=timezone,
            )
            session.add(history)
            session.commit()
            session.refresh(history)

            HistoryRepository._trim_old_history(link_id, session)

            return history.to_dict()
        finally:
            session.close()

    @staticmethod
    def _trim_old_history(link_id: int, session) -> None:
        count = session.query(History).filter_by(link_id=link_id).count()
        if count > 5:
            to_delete = (
                session.query(History)
                .filter_by(link_id=link_id)
                .order_by(History.checked_at.asc())
                .limit(count - 5)
                .all()
            )
            for h in to_delete:
                if h.screenshot:
                    try:
                        screenshot_dir = os.path.join(
                            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                            "static",
                            "screenshots",
                        )
                        screenshot_path = os.path.join(screenshot_dir, h.screenshot)
                        if os.path.exists(screenshot_path):
                            os.remove(screenshot_path)
                    except Exception:
                        pass
                session.delete(h)
            session.commit()

    @staticmethod
    def update_screenshot(history_id: int, filename: str) -> None:
        session = get_session()
        try:
            history = session.query(History).filter_by(id=history_id).first()
            if history:
                history.screenshot = filename
                session.commit()
        finally:
            session.close()
