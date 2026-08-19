"""Offline tests for the Pinecone ingestion ledger.

Run: python tests_ingestion_tracker.py
"""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from clients.pinecone_client import PineconeDB
from config.settings import EMBED_BATCH_SIZE
from pipeline.stage2_indexing.ingestion_tracker import IngestionTracker, chunk_fingerprint
from pipeline.stage2_indexing import orchestrator
from pipeline.stage2_indexing.vector_metadata import pinecone_metadata
from pipeline.stage3_retrieval.local_chunks import LocalChunkStore
from pipeline.stage3_retrieval.retrievers.hierarchical import HierarchicalRetriever
from pipeline.stage3_retrieval.retrievers.vector import VectorRetriever
from utils.adaptive_batch import (
    AdaptiveBatchPolicy,
    is_capacity_error,
    run_adaptive_batches,
)


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
            delete_calls = 0
            events = []

            def set_namespace(self, namespace):
                self.namespace = namespace

            def initialize_db(self):
                return self.index_created

            def store_documents(self, chunks):
                self.store_calls += 1
                self.events.append("store")

            def delete_documents(self, chunks):
                self.delete_calls += 1
                self.events.append(("delete", [chunk["id"] for chunk in chunks]))

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
            self.assertEqual(1, embedder.delete_calls)
            self.assertEqual(
                [("delete", ["a", "b"]), "store"],
                embedder.events,
            )

            # If Pinecone reports that this index was newly created, stale
            # records are discarded and the exact same chunks are embedded.
            embedder.index_created = True
            orchestrator.run_ingestion(**kwargs)
            self.assertEqual(2, embedder.store_calls)
            self.assertEqual(1, embedder.delete_calls)

    def test_pinecone_upserts_in_batches_of_40(self):
        db = PineconeDB.__new__(PineconeDB)
        calls = []
        db.index = SimpleNamespace(
            upsert=lambda *, vectors, namespace: calls.append((vectors, namespace))
        )
        vectors = [{"id": str(i)} for i in range(95)]

        db.upsert_vectors(vectors, namespace="baseline")

        self.assertEqual([40, 40, 15], [len(batch) for batch, _ in calls])
        self.assertTrue(all(namespace == "baseline" for _, namespace in calls))

    def test_pinecone_upsert_reduces_batch_after_capacity_error(self):
        class CapacityError(RuntimeError):
            status_code = 429

        attempted_sizes = []

        def upsert(*, vectors, namespace):
            attempted_sizes.append(len(vectors))
            if len(vectors) > 20:
                raise CapacityError("RESOURCE_EXHAUSTED")

        db = PineconeDB.__new__(PineconeDB)
        db.index = SimpleNamespace(upsert=upsert)
        vectors = [{"id": str(i)} for i in range(55)]

        with patch("utils.adaptive_batch.time.sleep") as sleep:
            db.upsert_vectors(vectors, namespace="baseline")

        self.assertEqual([40, 20, 20, 15], attempted_sizes)
        sleep.assert_called_once_with(2.0)

    def test_failed_partial_ingestion_is_cleaned_before_retry(self):
        class FakeEmbedder:
            model = "gemini-embedding-001"
            dimension = 3072
            vector_db = SimpleNamespace(index_name="index-a")
            store_calls = 0
            delete_calls = 0

            def set_namespace(self, namespace):
                self.namespace = namespace

            def initialize_db(self):
                return False

            def delete_documents(self, chunks):
                self.delete_calls += 1

            def store_documents(self, chunks):
                self.store_calls += 1
                if self.store_calls == 1:
                    raise RuntimeError("simulated partial Pinecone upsert")

        embedder = FakeEmbedder()
        json_path = str(Path(self.temp_dir.name) / "structured_output.json")
        patches = (
            patch.object(orchestrator, "discover_plugins"),
            patch.object(orchestrator.EMBEDDERS, "build", return_value=embedder),
            patch.object(orchestrator.CHUNKERS, "build", return_value=object()),
            patch.object(orchestrator, "chunk_document", return_value=self.chunks),
            patch.object(orchestrator, "IngestionTracker", return_value=self.tracker),
            patch.object(orchestrator, "_remove_bm25_chunk_ids", return_value=2),
            patch.object(orchestrator, "_update_bm25_index"),
        )
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            patches[4],
            patches[5] as remove_bm25,
            patches[6] as update_bm25,
        ):
            kwargs = {
                "json_path": json_path,
                "embedder_name": "gemini",
                "chunker_name": "baseline",
                "update_bm25": True,
            }
            with self.assertRaisesRegex(RuntimeError, "partial Pinecone upsert"):
                orchestrator.run_ingestion(**kwargs)

            self.assertIsNone(
                self.tracker.get_record(
                    index_name="index-a",
                    namespace="baseline",
                    document=orchestrator.document_key(json_path),
                )
            )
            self.assertEqual(1, remove_bm25.call_count)
            update_bm25.assert_not_called()
            orchestrator.run_ingestion(**kwargs)

            self.assertEqual(2, remove_bm25.call_count)
            update_bm25.assert_called_once()

        self.assertEqual(2, embedder.delete_calls)
        self.assertEqual(2, embedder.store_calls)
        self.assertIsNotNone(
            self.tracker.get_record(
                index_name="index-a",
                namespace="baseline",
                document=orchestrator.document_key(json_path),
            )
        )

    def test_bm25_cleanup_removes_only_requested_chunk_ids(self):
        class FakeBM25:
            instances = []

            def __init__(self):
                self._metadatas = []
                self.built = None
                self.saved = None
                self.instances.append(self)

            def load(self, path):
                self._metadatas = [
                    {"id": "a", "subsection_text": "A"},
                    {"id": "b", "subsection_text": "B"},
                    {"id": "other", "subsection_text": "OTHER"},
                ]
                return True

            def build(self, chunks):
                self.built = chunks

            def save(self, path):
                self.saved = path

        index_path = Path(self.temp_dir.name) / "bm25.pkl"
        with patch.object(orchestrator, "BM25Index", FakeBM25):
            removed = orchestrator._remove_bm25_chunk_ids({"a", "b"}, index_path)

        self.assertEqual(2, removed)
        rebuilt = FakeBM25.instances[1]
        self.assertEqual(["other"], [chunk["id"] for chunk in rebuilt.built])
        self.assertEqual(index_path, rebuilt.saved)

    def test_pinecone_deletes_large_id_sets_in_batches(self):
        db = PineconeDB.__new__(PineconeDB)
        calls = []
        db.index = SimpleNamespace(
            delete=lambda *, ids, namespace: calls.append((ids, namespace))
        )
        ids = [str(i) for i in range(2005)]

        db.delete_vectors(ids, namespace="baseline")

        self.assertEqual([1000, 1000, 5], [len(batch) for batch, _ in calls])
        self.assertEqual(ids, [item for batch, _ in calls for item in batch])

    def test_adaptive_batch_reduces_and_keeps_smaller_size(self):
        attempted_sizes = []

        def process(batch):
            attempted_sizes.append(len(batch))
            if len(batch) > 4:
                raise RuntimeError("429 RESOURCE_EXHAUSTED: token quota exceeded")
            return list(batch)

        results = run_adaptive_batches(
            list(range(11)),
            process,
            policy=AdaptiveBatchPolicy(
                initial_batch_size=8,
                initial_backoff_seconds=0,
            ),
            operation="test embedding",
            logger=__import__("logging").getLogger("AdaptiveBatchTest"),
        )

        self.assertEqual([8, 4, 4, 3], attempted_sizes)
        self.assertEqual(list(range(11)), [item for batch in results for item in batch])
        self.assertEqual(64, EMBED_BATCH_SIZE["gemini"])

    def test_adaptive_batch_does_not_hide_unrelated_errors(self):
        with self.assertRaisesRegex(ValueError, "bad credentials"):
            run_adaptive_batches(
                [1, 2, 3],
                lambda _batch: (_ for _ in ()).throw(ValueError("bad credentials")),
                policy=AdaptiveBatchPolicy(
                    initial_batch_size=3,
                    initial_backoff_seconds=0,
                ),
                operation="test embedding",
                logger=__import__("logging").getLogger("AdaptiveBatchTest"),
            )

        self.assertTrue(is_capacity_error(RuntimeError("ResourceExhausted: 429")))
        self.assertFalse(is_capacity_error(ValueError("invalid model name")))

    def test_pinecone_metadata_excludes_local_text_without_mutating_chunk(self):
        chunk = {
            "id": "chunk-a",
            "metadata": {
                "doc_name": "Document A",
                "section": "Licensing",
                "subsection_text": "retrievable chunk",
                "full_subsection_text": "complete original subsection",
                "bm25_text": "sparse-search text",
            },
        }

        compact = pinecone_metadata(chunk)

        self.assertEqual(
            {"doc_name": "Document A", "section": "Licensing"},
            compact,
        )
        self.assertIn("subsection_text", chunk["metadata"])
        self.assertIn("full_subsection_text", chunk["metadata"])
        self.assertIn("bm25_text", chunk["metadata"])

    def test_dense_retrievers_enrich_pinecone_matches_from_local_json(self):
        chunks_dir = Path(self.temp_dir.name) / "doc-a"
        chunks_dir.mkdir()
        cache_path = chunks_dir / "structured_output_chunks__baseline.json"
        cache_path.write_text(
            json.dumps(
                [
                    {
                        "id": "chunk-a",
                        "text": "embedding text",
                        "metadata": {
                            "subsection_text": "local chunk text",
                            "full_subsection_text": "local complete subsection",
                            "bm25_text": "local BM25 text",
                        },
                    }
                ]
            ),
            encoding="utf-8",
        )
        local_store = LocalChunkStore(chunker="baseline", root=self.temp_dir.name)
        result = {
            "matches": [
                {
                    "id": "chunk-a",
                    "score": 0.75,
                    "metadata": {"doc_name": "Document A", "section": "Licensing"},
                }
            ]
        }

        vector = VectorRetriever(chunker="baseline", local_store=local_store)
        vector.set_embedder(SimpleNamespace(search=lambda query, top_k: result))
        vector_chunk = vector.search("licence", top_k=1)[0]

        hierarchical = HierarchicalRetriever(
            chunker="baseline",
            local_store=local_store,
        )
        hierarchical_chunk = hierarchical._matches_to_dicts(result)[0]

        for enriched in (vector_chunk, hierarchical_chunk):
            self.assertEqual("local chunk text", enriched["subsection_text"])
            self.assertEqual(
                "local complete subsection",
                enriched["full_subsection_text"],
            )
            self.assertEqual("local BM25 text", enriched["bm25_text"])
            self.assertEqual("Document A", enriched["doc_name"])
            self.assertEqual(0.75, enriched["score"])

    def test_hierarchical_neighbor_text_is_enriched_from_local_json(self):
        chunks_dir = Path(self.temp_dir.name) / "doc-a"
        chunks_dir.mkdir()
        (chunks_dir / "structured_output_chunks__baseline.json").write_text(
            json.dumps(
                [
                    {
                        "id": "hit",
                        "metadata": {
                            "subsection_text": "ACTUAL",
                            "bm25_text": "ACTUAL",
                        },
                    },
                    {
                        "id": "previous",
                        "metadata": {
                            "subsection_text": "PREVIOUS LOCAL TEXT",
                            "bm25_text": "PREVIOUS LOCAL TEXT",
                        },
                    },
                ]
            ),
            encoding="utf-8",
        )
        retriever = HierarchicalRetriever(
            chunker="baseline",
            local_store=LocalChunkStore(chunker="baseline", root=self.temp_dir.name),
        )
        retriever._embedder = SimpleNamespace(
            fetch_vectors=lambda ids: {
                "previous": {"values": [1.0, 0.0], "metadata": {}}
            }
        )
        chunk = {
            "id": "hit",
            "subsection_text": "ACTUAL",
            "score": 0.5,
            "base_score": 0.5,
            "prev_ids": ["previous"],
            "next_ids": [],
        }

        enriched = retriever._expand_one_neighbor(chunk, [1.0, 0.0])

        self.assertTrue(enriched["neighbor_expanded"])
        self.assertIn("PREVIOUS LOCAL TEXT", enriched["subsection_text"])
        self.assertIn("ACTUAL", enriched["subsection_text"])


if __name__ == "__main__":
    unittest.main()
