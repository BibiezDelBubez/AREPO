"""
Database models for AREPO (Enigmistica Suite).
Provides SQLAlchemy schemas for words, definitions, and user overrides.
"""

from typing import List, Optional
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Word(Base):
    """Core Word model representing entries in the dictionary."""
    __tablename__ = 'words'

    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(100), unique=True, nullable=False, index=True)
    length = Column(Integer, nullable=False, index=True)
    vowel_pattern = Column(String(100), nullable=True)  # e.g. "CVCV"
    rarity = Column(Integer, default=1, index=True)      # 1 (Common) to 5 (Obscure)
    category = Column(String(50), default="Sostantivo", index=True)  # Sostantivo, Verbo, Aggettivo, Avverbio, Altro
    is_flexed = Column(Boolean, default=False)
    is_proper_name = Column(Boolean, default=False)
    tags = Column(String(200), nullable=True)
    is_excluded = Column(Boolean, default=False, index=True)  # Blacklist flag

    definitions = relationship("Definition", back_populates="word", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Word(term='{self.term}', length={self.length}, category='{self.category}')>"


class Definition(Base):
    """Clues / Definitions associated with words."""
    __tablename__ = 'definitions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word_id = Column(Integer, ForeignKey('words.id', ondelete="CASCADE"), nullable=False, index=True)
    clue = Column(Text, nullable=False)
    author = Column(String(100), default="Sistema")  # "Sistema" or "Utente"
    is_favorite = Column(Boolean, default=False)

    word = relationship("Word", back_populates="definitions")

    def __repr__(self) -> str:
        return f"<Definition(clue='{self.clue[:30]}...', author='{self.author}')>"


class UserWord(Base):
    """Custom words or notes added by the user in user_dictionary.sqlite."""
    __tablename__ = 'user_words'

    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(100), unique=True, nullable=False, index=True)
    length = Column(Integer, nullable=False, index=True)
    category = Column(String(50), default="Sostantivo")
    custom_clue = Column(Text, nullable=True)
    is_blacklisted = Column(Boolean, default=False)
    created_at = Column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<UserWord(term='{self.term}')>"
