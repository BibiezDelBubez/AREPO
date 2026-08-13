"""
Dual-layer database connection manager for AREPO.
Handles simultaneous access to core_dictionary.sqlite (Read-Only) and user_dictionary.sqlite (Read-Write).
"""

import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from core.database.models import Base, Word, UserWord, Definition


class DatabaseManager:
    """Manages SQLite database engines and session factories."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base_dir, "data")
        
        os.makedirs(data_dir, exist_ok=True)
        self.core_db_path = os.path.join(data_dir, "core_dictionary.sqlite")
        self.user_db_path = os.path.join(data_dir, "user_dictionary.sqlite")

        # Core DB Engine (read-write during build script, read-only at runtime)
        self.core_engine = create_engine(f"sqlite:///{self.core_db_path}", echo=False)
        self.CoreSession = sessionmaker(bind=self.core_engine)

        # User DB Engine (read-write)
        self.user_engine = create_engine(f"sqlite:///{self.user_db_path}", echo=False)
        self.UserSession = sessionmaker(bind=self.user_engine)

        self.init_databases()

    def init_databases(self) -> None:
        """Create tables if they do not exist."""
        Base.metadata.create_all(self.core_engine)
        Base.metadata.create_all(self.user_engine)

    def get_core_session(self) -> Session:
        """Return a new session for the core dictionary."""
        return self.CoreSession()

    def get_user_session(self) -> Session:
        """Return a new session for the user dictionary."""
        return self.UserSession()
