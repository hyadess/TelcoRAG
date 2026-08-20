"""Restore chunker artifacts from PostgreSQL into Vercel's temporary cache."""

import gzip
import hashlib
import os
from pathlib import Path

from tool.backend.chunk_tables import chunker_slug
from utils.database_url import psycopg_database_url


def restore_bm25_index(chunker: str, destination: Path) -> bool:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to restore the BM25 index")

    import psycopg

    with psycopg.connect(
        psycopg_database_url(database_url), prepare_threshold=None
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT sha256, compression, payload
                FROM chunk_artifacts
                WHERE chunker = %s AND artifact_name = 'bm25_index'
                """,
                (chunker_slug(chunker),),
            )
            row = cursor.fetchone()
    if row is None:
        return False

    expected_sha256, compression, payload = row
    if compression != "gzip":
        raise RuntimeError(f"Unsupported BM25 artifact compression: {compression}")
    data = gzip.decompress(bytes(payload))
    actual_sha256 = hashlib.sha256(data).hexdigest()
    if actual_sha256 != expected_sha256:
        raise RuntimeError("Downloaded BM25 artifact failed its SHA-256 check")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(destination)
    return True
