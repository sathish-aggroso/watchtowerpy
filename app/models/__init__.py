from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    links = relationship("Link", back_populates="project")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False)
    title = Column(String(500), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    tags = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)

    project = relationship("Project", back_populates="links")
    initial_page = relationship("InitialPage", back_populates="link", uselist=False)
    diffs = relationship(
        "Diff", back_populates="link", order_by="desc(Diff.checked_at)"
    )

    def to_dict(self, include_project: bool = True) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "project_id": self.project_id,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_checked": self.last_checked.isoformat()
            if self.last_checked
            else None,
            "last_error": self.last_error,
            "is_active": self.is_active,
        }
        if include_project and self.project:
            result["project_name"] = self.project.name
        return result


class InitialPage(Base):
    __tablename__ = "initial_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False, unique=True)
    full_content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    screenshot = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    link = relationship("Link", back_populates="initial_page")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "link_id": self.link_id,
            "full_content": self.full_content,
            "content_hash": self.content_hash,
            "screenshot": self.screenshot,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Diff(Base):
    __tablename__ = "diffs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)
    previous_diff_id = Column(Integer, ForeignKey("diffs.id"), nullable=True)
    full_content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    diff_content = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text, nullable=True)
    price = Column(String(100), nullable=True)
    price_amount = Column(String(50), nullable=True)
    price_currency = Column(String(10), nullable=True)
    screenshot = Column(Text, nullable=True)
    timezone = Column(String(50), default="UTC")

    link = relationship("Link", back_populates="diffs")
    previous_diff = relationship("Diff", remote_side=[id])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "link_id": self.link_id,
            "previous_diff_id": self.previous_diff_id,
            "full_content": self.full_content,
            "content_hash": self.content_hash,
            "diff_content": self.diff_content,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
            "summary": self.summary,
            "price": self.price,
            "price_amount": self.price_amount,
            "price_currency": self.price_currency,
            "screenshot": self.screenshot,
            "timezone": self.timezone,
        }


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False)
    content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text, nullable=True)
    price = Column(String(100), nullable=True)
    price_amount = Column(String(50), nullable=True)
    price_currency = Column(String(10), nullable=True)
    screenshot = Column(Text, nullable=True)
    timezone = Column(String(50), default="UTC")

    link = relationship("Link")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "link_id": self.link_id,
            "content": self.content,
            "content_hash": self.content_hash,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
            "summary": self.summary,
            "price": self.price,
            "price_amount": self.price_amount,
            "price_currency": self.price_currency,
            "screenshot": self.screenshot,
            "timezone": self.timezone,
        }
