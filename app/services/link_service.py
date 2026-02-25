from typing import List, Dict, Any, Optional

from app.repositories import LinkRepository


class LinkService:
    @staticmethod
    def get_all_links(project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        return LinkRepository.get_all(project_id)

    @staticmethod
    def get_link(link_id: int) -> Optional[Dict[str, Any]]:
        return LinkRepository.get_by_id(link_id)

    @staticmethod
    def create_link(
        url: str,
        title: Optional[str] = None,
        project_id: int = 1,
        tags: Optional[str] = None,
    ) -> Dict[str, Any]:
        return LinkRepository.create(url, title, project_id, tags)

    @staticmethod
    def delete_link(link_id: int) -> bool:
        return LinkRepository.delete(link_id)
