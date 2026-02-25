from typing import List, Optional, Dict, Any

from app.models import Project, Link
from app.extensions import get_session


class ProjectRepository:
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        session = get_session()
        try:
            projects = session.query(Project).order_by(Project.name).all()
            return [p.to_dict() for p in projects]
        finally:
            session.close()

    @staticmethod
    def get_by_id(project_id: int) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            project = session.query(Project).filter_by(id=project_id).first()
            return project.to_dict() if project else None
        finally:
            session.close()

    @staticmethod
    def create(name: str, description: Optional[str] = None) -> Dict[str, Any]:
        session = get_session()
        try:
            project = Project(name=name, description=description)
            session.add(project)
            session.commit()
            session.refresh(project)
            return project.to_dict()
        finally:
            session.close()

    @staticmethod
    def delete(project_id: int) -> bool:
        session = get_session()
        try:
            project = session.query(Project).filter_by(id=project_id).first()
            if project and project.id != 1:
                session.query(Link).filter_by(project_id=project_id).update(
                    {Link.project_id: 1}
                )
                session.delete(project)
                session.commit()
                return True
            return False
        finally:
            session.close()
