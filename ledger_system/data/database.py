"""Database connection and session management"""
import os
from pathlib import Path
from typing import Generator

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

Base = declarative_base()

_DB_CONFIG = None


def load_config() -> dict:
    """Load database config from settings.yaml"""
    global _DB_CONFIG
    if _DB_CONFIG is None:
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        _DB_CONFIG = config["database"]
    return _DB_CONFIG


def get_engine():
    """Create SQLAlchemy engine"""
    cfg = load_config()
    url = f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['name']}"
    return create_engine(url, echo=False)


def get_session_factory():
    """Create session factory"""
    engine = get_engine()
    return sessionmaker(bind=engine)


class DatabaseSession:
    """Context manager for database session"""
    def __init__(self):
        self._session = None
        self._factory = None

    def __enter__(self):
        self._factory = get_session_factory()
        self._session = self._factory()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self._session.rollback()
        else:
            self._session.commit()
        self._session.close()
        return False


def get_session():
    """Get database session (context manager)"""
    return DatabaseSession()


def init_database():
    """Create all tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)