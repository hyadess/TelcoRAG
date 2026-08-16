"""Offline tests for the Pinecone ingestion ledger.

Run: python tests_ingestion_tracker.py
"""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pipeline.stage2_indexing.ingestion_tracker import IngestionTracker, chunk_fingerprint
from pipeline.stage2_indexing import orchestrator


class IngestionTrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tracker_path = Path(self.temp_dir.name) / "tracker.json"
        self.tracker = IngestionTracker(self.tracker_path)
        self.chunks = [
            {"id": "a", "text": "alpha", "metadata": {"page": 1}},
            {"id": "b", "text": "beta", "metadata": {"page": 2}},
        ]
        self.fingerprint = chunk_fingerprint(self.chunks)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _mark(self, *, index="index-a", namespace="baseline", document="doc-a"):
        self.tracker.mark_indexed(
            index_name=index,
            namespace=namespace,
            document=document,
            fingerprint=self.fingerprint,
            chunk_count=2,
            embedder="gemini",
            model="gemini-embedding-001",
            dimension=3072,
        )

    def _is_indexed(self, **overrides):
        values = {
            "index_name": "index-a",
            "namespace": "baseline",
            "document": "doc-a",
            "fingerprint": self.fingerprint,
            "chunk_count": 2,
            "embedder": "gemini",
            "model": "gemini-embedding-001",
            "dimension": 3072,
        }
        values.update(overrides)
        return self.tracker.is_indexed(**values)

    def test_exact_completed_chunk_set_is_skipped(self):
        self._mark()
        self.assertTrue(self._is_indexed())
        self.assertFalse(self._is_indexed(chunk_count=3))
        self.assertFalse(self._is_indexed(model="different-model"))
        self.assertFalse(self._is_indexed(namespace="different-namespace"))

    def test_changed_chunk_content_changes_fingerprint(self):
        changed = [dict(self.chunks[0]), dict(self.chunks[1], text="changed")]
        self.assertNotEqual(self.fingerprint, chunk_fingerprint(changed))

    def test_clear_index_does_not_clear_other_indexes(self):
        self._mark(document="doc-a")
        self._mark(document="doc-b")
        self._mark(index="index-b", document="doc-c")

        self.assertEqual(2, self.tracker.clear_index("index-a"))
        self.assertFalse(self._is_indexed())
        self.assertIsNotNone(
            self.tracker.get_record(
                index_name="index-b",
                namespace="baseline",
                document="doc-c",
            )
        )

        # The atomic writer always leaves a complete, valid JSON document.
        with self.tracker_path.open("r", encoding="utf-8") as handle:
            self.assertEqual(1, json.load(handle)["version"])

    def test_ingestion_skips_completed_document_and_retries_for_fresh_index(self):
        class FakeEmbedder:
            model = "gemini-embedding-001"
            dimension = 3072
            vector_db = SimpleNamespace(index_name="index-a")
            index_created = False
            store_calls = 0

            def set_namespace(self, namespace):
                self.namespace = namespace

            def initialize_db(self):
                return self.index_created

            def store_documents(self, chunks):
                self.store_calls += 1

        embedder = FakeEmbedder()
        patches = (
            patch.object(orchestrator, "discover_plugins"),
            patch.object(orchestrator.EMBEDDERS, "build", return_value=embedder),
            patch.object(orchestrator.CHUNKERS, "build", return_value=object()),
            patch.object(orchestrator, "chunk_document", return_value=self.chunks),
            patch.object(orchestrator, "IngestionTracker", return_value=self.tracker),
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            kwargs = {
                "json_path": str(Path(self.temp_dir.name) / "structured_output.json"),
                "embedder_name": "gemini",
                "chunker_name": "baseline",
                "update_bm25": False,
            }
            orchestrator.run_ingestion(**kwargs)
            orchestrator.run_ingestion(**kwargs)
            self.assertEqual(1, embedder.store_calls)

            # If Pinecone reports that this index was newly created, stale
            # records are discarded and the exact same chunks are embedded.
            embedder.index_created = True
            orchestrator.run_ingestion(**kwargs)
            self.assertEqual(2, embedder.store_calls)


if __name__ == "__main__":
    unittest.main()
