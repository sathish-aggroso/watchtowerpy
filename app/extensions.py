from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from app.models import Base

_engine = None
_Session = None


def init_extensions(app: "Flask") -> None:
    global _engine, _Session

    db_path = app.config.get("DATABASE_PATH", "./db/checkdiff.db")
    db_url = f"sqlite:///{db_path}"

    _engine = create_engine(
        db_url, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    _Session = scoped_session(sessionmaker(bind=_engine))

    Base.metadata.create_all(_engine)
    _seed_default_project()


def _seed_default_project() -> None:
    from app.models import Project

    session = _Session()
    try:
        existing = session.query(Project).filter_by(id=1).first()
        if not existing:
            default_project = Project(
                id=1,
                name="Default",
                description="Default project for ungrouped links",
            )
            session.add(default_project)
            session.commit()
    finally:
        session.close()


def get_session():
    global _Session
    if _Session is None:
        from app import create_app

        app = create_app()
    return _Session()


def get_raw_session():
    global _Session
    if _Session is None:
        from app import create_app

        app = create_app()
    return _Session()


def check_database_health() -> bool:
    global _Session
    if _Session is None:
        from app import create_app

        app = create_app()
    try:
        session = _Session()
        session.execute(text("SELECT 1"))
        session.close()
        return True
    except Exception:
        return False
