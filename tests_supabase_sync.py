"""Offline tests for per-chunker Supabase synchronization helpers."""

import json
import tempfile
import unittest
from pathlib import Path

from pipeline.stage3_retrieval.local_chunks import LocalChunkStore
from scripts.sync_supabase_chunks import discover_chunkers, file_sha256, rows_from_file
from tool.backend.chunk_tables import chunk_table_name
from utils.database_url import psycopg_database_url, sqlalchemy_database_url


class SupabaseSyncTests(unittest.TestCase):
    def test_chunker_table_names_are_stable_and_safe(self):
        self.assertEqual(chunk_table_name("baseline"), "chunk_baseline")
        self.assertEqual(chunk_table_name("Semantic-v2"), "chunk_semantic_v2")

    def test_database_urls_work_for_both_drivers(self):
        plain = "postgresql://user:password@host/database"
        sqlalchemy = "postgresql+psycopg://user:password@host/database"
        self.assertEqual(sqlalchemy_database_url(plain), sqlalchemy)
        self.assertEqual(psycopg_database_url(sqlalchemy), plain)

    def test_discovery_and_row_conversion_support_other_chunkers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "document"
            folder.mkdir()
            path = folder / "structured_output_chunks__semantic-v2.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": "chunk-1",
                            "metadata": {
                                "subsection_text": "full text",
                                "bm25_text": "keyword text",
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )

            self.assertEqual(discover_chunkers(root), ["semantic-v2"])
            rows = rows_from_file(path, f"document/{path.name}")
            self.assertEqual(rows[0]["full_subsection_text"], "full text")
            self.assertEqual(rows[0]["bm25_text"], "keyword text")
            self.assertEqual(len(file_sha256(path)), 64)

            store = LocalChunkStore(chunker="semantic-v2", root=root)
            enriched = store.enrich({"id": "chunk-1"})
            self.assertEqual(enriched["subsection_text"], "full text")


if __name__ == "__main__":
    unittest.main()
