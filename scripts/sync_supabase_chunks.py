"""Incrementally synchronize chunk JSON files and BM25 indexes to PostgreSQL."""

import argparse
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import MetaData, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from config.settings import bm25_index_path
from tool.backend.chunk_tables import chunk_table, chunker_slug
from tool.backend.database import Base, engine
from tool.backend.models import ChunkArtifact, ChunkUploadTracker


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def discover_chunkers(root: Path) -> list[str]:
    prefix = "structured_output_chunks__"
    return sorted(
        {
            path.stem.removeprefix(prefix)
            for path in root.glob(f"**/{prefix}*.json")
            if path.stem.removeprefix(prefix)
        }
    )


def rows_from_file(path: Path, source_file: str) -> list[dict]:
    chunks = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for chunk in chunks:
        metadata = chunk.get("metadata", {}) or {}
        subsection = str(metadata.get("subsection_text", "") or "")
        rows.append(
            {
                "chunk_id": str(chunk["id"]),
                "source_file": source_file,
                "subsection_text": subsection,
                "full_subsection_text": str(
                    metadata.get("full_subsection_text") or subsection
                ),
                "bm25_text": str(metadata.get("bm25_text") or subsection),
            }
        )
    return rows


def synchronize_chunker(
    root: Path,
    chunker: str,
    *,
    batch_size: int = 100,
    prune_missing: bool = False,
) -> tuple[int, int]:
    slug = chunker_slug(chunker)
    files = sorted(root.glob(f"**/structured_output_chunks__{chunker}.json"))
    if not files and not prune_missing:
        raise FileNotFoundError(
            f"No structured_output_chunks__{chunker}.json files found under {root}"
        )

    metadata = MetaData()
    table = chunk_table(metadata, slug)
    metadata.create_all(engine, tables=[table])
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        tracked = {
            record.source_file: record
            for record in session.scalars(
                select(ChunkUploadTracker).where(
                    ChunkUploadTracker.chunker == slug
                )
            )
        }

    uploaded_files = 0
    uploaded_rows = 0
    seen_files = set()
    for path in files:
        source_file = path.relative_to(root).as_posix()
        seen_files.add(source_file)
        sha256 = file_sha256(path)
        previous = tracked.get(source_file)
        if previous is not None and previous.sha256 == sha256:
            print(f"[{slug}] unchanged: {source_file}")
            continue

        rows = rows_from_file(path, source_file)
        now = datetime.now(timezone.utc)
        with Session(engine) as session:
            session.execute(delete(table).where(table.c.source_file == source_file))
            for offset in range(0, len(rows), batch_size):
                batch = rows[offset : offset + batch_size]
                statement = insert(table).values(batch)
                statement = statement.on_conflict_do_update(
                    index_elements=[table.c.chunk_id],
                    set_={
                        "source_file": statement.excluded.source_file,
                        "subsection_text": statement.excluded.subsection_text,
                        "full_subsection_text": statement.excluded.full_subsection_text,
                        "bm25_text": statement.excluded.bm25_text,
                    },
                )
                session.execute(statement)

            tracker = insert(ChunkUploadTracker).values(
                chunker=slug,
                source_file=source_file,
                sha256=sha256,
                file_size=path.stat().st_size,
                row_count=len(rows),
                updated_at=now,
            )
            tracker = tracker.on_conflict_do_update(
                index_elements=[
                    ChunkUploadTracker.chunker,
                    ChunkUploadTracker.source_file,
                ],
                set_={
                    "sha256": tracker.excluded.sha256,
                    "file_size": tracker.excluded.file_size,
                    "row_count": tracker.excluded.row_count,
                    "updated_at": tracker.excluded.updated_at,
                },
            )
            session.execute(tracker)
            session.commit()

        verb = "updated" if previous is not None else "uploaded"
        print(f"[{slug}] {verb}: {source_file} ({len(rows)} chunks)")
        uploaded_files += 1
        uploaded_rows += len(rows)

    missing = sorted(set(tracked) - seen_files)
    if missing and not prune_missing:
        print(
            f"[{slug}] {len(missing)} tracked file(s) are absent locally; "
            "kept in Supabase (use --prune-missing to remove them)."
        )
    elif missing:
        with Session(engine) as session:
            for source_file in missing:
                session.execute(delete(table).where(table.c.source_file == source_file))
                session.execute(
                    delete(ChunkUploadTracker).where(
                        ChunkUploadTracker.chunker == slug,
                        ChunkUploadTracker.source_file == source_file,
                    )
                )
                print(f"[{slug}] pruned: {source_file}")
            session.commit()

    return uploaded_files, uploaded_rows


def synchronize_bm25(chunker: str) -> bool:
    slug = chunker_slug(chunker)
    path = bm25_index_path(chunker)
    if not path.is_file():
        print(f"[{slug}] BM25 index not found, skipped: {path}")
        return False

    sha256 = file_sha256(path)
    with Session(engine) as session:
        existing = session.get(ChunkArtifact, (slug, "bm25_index"))
        if existing is not None and existing.sha256 == sha256:
            print(f"[{slug}] BM25 index unchanged")
            return False

    raw = path.read_bytes()
    compressed = gzip.compress(raw, compresslevel=6, mtime=0)
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        statement = insert(ChunkArtifact).values(
            chunker=slug,
            artifact_name="bm25_index",
            sha256=sha256,
            compression="gzip",
            source_size=len(raw),
            stored_size=len(compressed),
            payload=compressed,
            updated_at=now,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[ChunkArtifact.chunker, ChunkArtifact.artifact_name],
            set_={
                "sha256": statement.excluded.sha256,
                "compression": statement.excluded.compression,
                "source_size": statement.excluded.source_size,
                "stored_size": statement.excluded.stored_size,
                "payload": statement.excluded.payload,
                "updated_at": statement.excluded.updated_at,
            },
        )
        session.execute(statement)
        session.commit()
    print(
        f"[{slug}] BM25 index uploaded "
        f"({len(raw) / 1024 / 1024:.1f} MiB -> {len(compressed) / 1024 / 1024:.1f} MiB)"
    )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synchronize chunk JSON files and BM25 indexes to Supabase."
    )
    parser.add_argument(
        "--root", type=Path, default=Path("knowledge_base/documents")
    )
    parser.add_argument(
        "--chunker",
        action="append",
        help="Chunker name to sync; repeat for multiple chunkers (default: baseline).",
    )
    parser.add_argument(
        "--all-chunkers",
        action="store_true",
        help="Discover and sync every structured_output_chunks__<chunker>.json variant.",
    )
    parser.add_argument(
        "--prune-missing",
        action="store_true",
        help="Delete database rows for tracked JSON files no longer present locally.",
    )
    parser.add_argument(
        "--skip-bm25", action="store_true", help="Do not upload BM25 indexes."
    )
    args = parser.parse_args()

    if args.all_chunkers and args.chunker:
        parser.error("Use either --all-chunkers or --chunker, not both")
    chunkers = discover_chunkers(args.root) if args.all_chunkers else args.chunker
    chunkers = chunkers or ["baseline"]
    if not chunkers:
        parser.error(f"No chunk JSON variants found under {args.root}")

    total_files = 0
    total_rows = 0
    for chunker in chunkers:
        files, rows = synchronize_chunker(
            args.root, chunker, prune_missing=args.prune_missing
        )
        total_files += files
        total_rows += rows
        if not args.skip_bm25:
            synchronize_bm25(chunker)
    print(
        f"Finished: {total_files} changed file(s), {total_rows} uploaded chunk row(s)."
    )


if __name__ == "__main__":
    main()
