"""Upload local chunk text to the PostgreSQL database used by the web tool."""

import argparse
import json
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from tool.backend.database import Base, engine
from tool.backend.models import RagChunk


def iter_rows(root: Path, chunker: str):
    pattern = f"**/structured_output_chunks__{chunker}.json"
    for path in sorted(root.glob(pattern)):
        for chunk in json.loads(path.read_text(encoding="utf-8")):
            metadata = chunk.get("metadata", {}) or {}
            subsection = str(metadata.get("subsection_text", "") or "")
            yield {
                "chunker": chunker,
                "chunk_id": str(chunk["id"]),
                "subsection_text": subsection,
                "full_subsection_text": str(
                    metadata.get("full_subsection_text") or subsection
                ),
                "bm25_text": str(metadata.get("bm25_text") or subsection),
            }


def seed(root: Path, chunker: str, batch_size: int = 250) -> int:
    Base.metadata.create_all(bind=engine)
    total = 0
    batch = []
    with Session(engine) as session:
        for row in iter_rows(root, chunker):
            batch.append(row)
            if len(batch) < batch_size:
                continue
            _upsert(session, batch)
            total += len(batch)
            batch.clear()
            print(f"Uploaded {total} chunks", flush=True)
        if batch:
            _upsert(session, batch)
            total += len(batch)
    return total


def _upsert(session: Session, rows: list[dict]) -> None:
    statement = insert(RagChunk).values(rows)
    statement = statement.on_conflict_do_update(
        index_elements=[RagChunk.chunker, RagChunk.chunk_id],
        set_={
            "subsection_text": statement.excluded.subsection_text,
            "full_subsection_text": statement.excluded.full_subsection_text,
            "bm25_text": statement.excluded.bm25_text,
        },
    )
    session.execute(statement)
    session.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path("knowledge_base/documents")
    )
    parser.add_argument("--chunker", default="baseline")
    args = parser.parse_args()
    total = seed(args.root, args.chunker)
    print(f"Finished: {total} chunks uploaded")


if __name__ == "__main__":
    main()
