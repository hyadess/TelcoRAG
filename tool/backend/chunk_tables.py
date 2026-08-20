"""Safe names and SQLAlchemy definitions for per-chunker text tables."""

import re

from sqlalchemy import Column, MetaData, String, Table, Text


def chunker_slug(chunker: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", chunker.strip().lower()).strip("_")
    if not slug:
        raise ValueError(f"Invalid chunker name: {chunker!r}")
    if len(slug) > 48:
        raise ValueError("Chunker name is too long for a PostgreSQL table name")
    return slug


def chunk_table_name(chunker: str) -> str:
    return f"chunk_{chunker_slug(chunker)}"


def chunk_table(metadata: MetaData, chunker: str) -> Table:
    return Table(
        chunk_table_name(chunker),
        metadata,
        Column("chunk_id", String(128), primary_key=True),
        Column("source_file", Text, nullable=False, index=True),
        Column("subsection_text", Text, nullable=False, default=""),
        Column("full_subsection_text", Text, nullable=False, default=""),
        Column("bm25_text", Text, nullable=False, default=""),
        extend_existing=True,
    )
