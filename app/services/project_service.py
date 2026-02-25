from typing import List, Dict, Any, Optional

from app.repositories import ProjectRepository


class ProjectService:
    @staticmethod
    def get_all_projects() -> List[Dict[str, Any]]:
        return ProjectRepository.get_all()

    @staticmethod
    def create_project(name: str, description: Optional[str] = None) -> Dict[str, Any]:
        return ProjectRepository.create(name, description)

    @staticmethod
    def delete_project(project_id: int) -> bool:
        return ProjectRepository.delete(project_id)
