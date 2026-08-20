"""Database engine and session lifecycle."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from tool.settings import SETTINGS


class Base(DeclarativeBase):
    pass


def sqlalchemy_database_url(url: str) -> str:
    """Normalize provider URLs to SQLAlchemy's psycopg v3 dialect."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


engine_options = {"pool_pre_ping": True}
if os.getenv("VERCEL"):
    # Supavisor already pools connections. Avoid keeping client-side pools in
    # short-lived serverless instances.
    engine_options["poolclass"] = NullPool
if "postgresql+psycopg" in sqlalchemy_database_url(SETTINGS.database_url):
    # Supabase transaction pooling does not support prepared statements.
    engine_options["connect_args"] = {"prepare_threshold": None}

engine = create_engine(sqlalchemy_database_url(SETTINGS.database_url), **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
