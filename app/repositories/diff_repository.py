import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models import InitialPage, Diff
from app.extensions import get_session


class InitialPageRepository:
    @staticmethod
    def get_by_link(link_id: int) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            initial = session.query(InitialPage).filter_by(link_id=link_id).first()
            return initial.to_dict() if initial else None
        finally:
            session.close()

    @staticmethod
    def create(
        link_id: int,
        full_content: str,
        content_hash: str,
        screenshot: Optional[str] = None,
    ) -> Dict[str, Any]:
        session = get_session()
        try:
            initial = InitialPage(
                link_id=link_id,
                full_content=full_content,
                content_hash=content_hash,
                screenshot=screenshot,
            )
            session.add(initial)
            session.commit()
            session.refresh(initial)
            return initial.to_dict()
        finally:
            session.close()

    @staticmethod
    def update_screenshot(link_id: int, filename: str) -> None:
        session = get_session()
        try:
            initial = session.query(InitialPage).filter_by(link_id=link_id).first()
            if initial:
                initial.screenshot = filename
                session.commit()
        finally:
            session.close()

    @staticmethod
    def delete_by_link(link_id: int) -> None:
        session = get_session()
        try:
            session.query(InitialPage).filter_by(link_id=link_id).delete()
            session.commit()
        finally:
            session.close()


class DiffRepository:
    @staticmethod
    def get_by_link(link_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        session = get_session()
        try:
            diffs = (
                session.query(Diff)
                .filter_by(link_id=link_id)
                .order_by(Diff.checked_at.desc())
                .limit(limit)
                .all()
            )
            return [d.to_dict() for d in diffs]
        finally:
            session.close()

    @staticmethod
    def get_by_id(diff_id: int) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            diff = session.query(Diff).filter_by(id=diff_id).first()
            return diff.to_dict() if diff else None
        finally:
            session.close()

    @staticmethod
    def get_latest(link_id: int) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            diff = (
                session.query(Diff)
                .filter_by(link_id=link_id)
                .order_by(Diff.id.desc())
                .first()
            )
            return diff.to_dict() if diff else None
        finally:
            session.close()

    @staticmethod
    def get_previous(diff_id: int) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            diff = session.query(Diff).filter_by(id=diff_id).first()
            if diff and diff.previous_diff_id:
                prev = session.query(Diff).filter_by(id=diff.previous_diff_id).first()
                return prev.to_dict() if prev else None
            return None
        finally:
            session.close()

    @staticmethod
    def create(
        link_id: int,
        previous_diff_id: Optional[int],
        full_content: str,
        content_hash: str,
        diff_content: Optional[str] = None,
        summary: Optional[str] = None,
        price: Optional[str] = None,
        price_amount: Optional[str] = None,
        price_currency: Optional[str] = None,
        screenshot: Optional[str] = None,
        timezone: str = "UTC",
    ) -> Dict[str, Any]:
        session = get_session()
        try:
            diff = Diff(
                link_id=link_id,
                previous_diff_id=previous_diff_id,
                full_content=full_content,
                content_hash=content_hash,
                diff_content=diff_content,
                summary=summary,
                price=price,
                price_amount=price_amount,
                price_currency=price_currency,
                screenshot=screenshot,
                timezone=timezone,
            )
            session.add(diff)
            session.commit()
            session.refresh(diff)
            return diff.to_dict()
        finally:
            session.close()

    @staticmethod
    def update_screenshot(diff_id: int, filename: str) -> None:
        session = get_session()
        try:
            diff = session.query(Diff).filter_by(id=diff_id).first()
            if diff:
                diff.screenshot = filename
                session.commit()
        finally:
            session.close()

    @staticmethod
    def delete_by_link(link_id: int) -> None:
        session = get_session()
        try:
            session.query(Diff).filter_by(link_id=link_id).delete()
            session.commit()
        finally:
            session.close()
