from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import joinedload

from app.models import Link
from app.extensions import get_session
from app.repositories.diff_repository import DiffRepository, InitialPageRepository


class LinkRepository:
    @staticmethod
    def get_all(project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        session = get_session()
        try:
            query = session.query(Link).options(joinedload(Link.project))
            if project_id:
                query = query.filter(Link.project_id == project_id)
            links = query.order_by(Link.last_checked.desc()).all()
            result = []
            for link in links:
                project_name = link.project.name if link.project else "Default"
                link_id = link.id

                initial_page = InitialPageRepository.get_by_link(link_id)
                latest_diff = DiffRepository.get_latest(link_id)

                last_checked = None
                if latest_diff:
                    last_checked = latest_diff.get("checked_at")
                elif initial_page:
                    last_checked = initial_page.get("checked_at")

                link_dict = link.to_dict()
                link_dict["project_name"] = project_name
                link_dict["last_checked"] = last_checked
                result.append(link_dict)
            return result
        finally:
            session.close()

    @staticmethod
    def get_by_id(link_id: int) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            link = (
                session.query(Link)
                .options(joinedload(Link.project))
                .filter_by(id=link_id)
                .first()
            )
            if link:
                project_name = link.project.name if link.project else "Default"
                last_checked = None

                initial_page = InitialPageRepository.get_by_link(link_id)
                latest_diff = DiffRepository.get_latest(link_id)

                if latest_diff:
                    last_checked = latest_diff.get("checked_at")
                elif initial_page:
                    last_checked = initial_page.get("checked_at")

                link_dict = link.to_dict()
                link_dict["project_name"] = project_name
                link_dict["last_checked"] = last_checked
                return link_dict
            return None
        finally:
            session.close()

    @staticmethod
    def create(
        url: str,
        title: Optional[str] = None,
        project_id: int = 1,
        tags: Optional[str] = None,
    ) -> Dict[str, Any]:
        session = get_session()
        try:
            link = Link(url=url, title=title or url, project_id=project_id, tags=tags)
            session.add(link)
            session.commit()
            session.refresh(link)
            return link.to_dict()
        finally:
            session.close()

    @staticmethod
    def update(link_id: int, **kwargs: Any) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            link = session.query(Link).filter_by(id=link_id).first()
            if link:
                for key, value in kwargs.items():
                    if hasattr(link, key):
                        if key == "last_checked" and isinstance(value, str):
                            value = datetime.fromisoformat(value)
                        setattr(link, key, value)
                session.commit()
                session.refresh(link)
                return link.to_dict()
            return None
        finally:
            session.close()

    @staticmethod
    def delete(link_id: int) -> bool:
        from app.repositories.diff_repository import (
            InitialPageRepository,
            DiffRepository,
        )

        session = get_session()
        try:
            InitialPageRepository.delete_by_link(link_id)
            DiffRepository.delete_by_link(link_id)

            link = session.query(Link).filter_by(id=link_id).first()
            if link:
                session.delete(link)
                session.commit()
                return True
            return False
        finally:
            session.close()
