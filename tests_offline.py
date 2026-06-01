"""
Offline smoke test — no network, no API keys.

Stubs the vendor SDKs so the whole plugin graph imports, then asserts the new
design:

  - registries: single `baseline` chunker; four reformulation operators
    (decompose / diversify / abstract / hyde) + the `simple` control;
    `hierarchical` retriever.
  - baseline chunker: dense embed text = headers + summary + subsection;
    BM25 corpus text = subsection text only (no enrichment).
  - chunk sequencing: seq / prev_ids / next_ids assigned in reading order.
  - BM25 index tokenizes the chunker-provided bm25_text.
  - hierarchical_ops: multi-level (doc -> chapter -> section) filtering;
    neighbour-expansion decision helpers (classify / select / continuation / cosine).
  - HierarchicalRetriever: sibling + neighbour expansion end-to-end against a
    fake embedder.
  - two-call gap analysis degrades gracefully to "sufficient" without an LLM.

Run:  python tests_offline.py
"""

import sys
import types

PROJECT_ROOT = __import__("pathlib").Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


# --- stub heavy vendor SDKs ------------------------------------------------
class _AnyMeta(type):
    def __getattr__(cls, _name):
        return _Any


class _Any(metaclass=_AnyMeta):
    def __init__(self, *a, **k): pass
    def __getattr__(self, _): return _Any
    def __call__(self, *a, **k): return _Any()


def _stub(name):
    m = types.ModuleType(name)
    m.__getattr__ = lambda _n: _Any
    sys.modules[name] = m
    return m


for _name in [
    "dotenv", "google", "google.genai", "openai", "cohere",
    "voyageai", "perplexityai", "pinecone", "llama_cloud_services",
]:
    _stub(_name)
sys.modules["dotenv"].load_dotenv = lambda *a, **k: None


# --- imports ---------------------------------------------------------------
from core.registry import CHUNKERS, QUERY_STRATEGIES, RETRIEVERS, discover_plugins
from core.schemas import GapAnalysis
from pipeline.stage2_indexing.bm25_index import BM25Index
from pipeline.stage2_indexing.sequencing import assign_neighbors
from pipeline.stage3_retrieval.refinement import analyze_gap
from pipeline.stage3_retrieval.retrievers.hierarchical_ops import (
    apply_levels, build_continuation, classify_relevance, cosine,
    group_by, level_key, rank_groups, select_passing_neighbors,
)

PASS, FAIL = 0, 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}")


SUB = {
    "document_name": "Telecom Act",
    "document_summary": "An act regulating telecom.",
    "chapter": "Chapter II",
    "section": "Licensing",
    "subsection_id": "4.05",
    "subsection_text": "The Licensee shall pay an annual fee within thirty days.",
    "page_numbers": [12],
}

print("== registry ==")
discover_plugins()
check("single baseline chunker", set(CHUNKERS.list()) == {"baseline"})
check("four operators + simple registered",
      set(QUERY_STRATEGIES.list()) == {"simple", "decompose", "diversify", "abstract", "hyde"})
check("hierarchical retriever registered", "hierarchical" in RETRIEVERS.list())

print("== baseline chunker (no enrichment) ==")
chunker = CHUNKERS.build("baseline")
c = chunker.process_subsection(SUB)[0]
check("embed text has summary + headers + subsection",
      "An act regulating telecom." in c["text"]
      and "Chapter: Chapter II" in c["text"]
      and SUB["subsection_text"] in c["text"])
check("bm25_text == subsection only", c["metadata"]["bm25_text"].strip() == SUB["subsection_text"])
check("no enrichment fields in metadata",
      not any(k in c["metadata"] for k in ("defined_terms", "cross_references", "key_facts")))

print("== chunk sequencing ==")
chunks = [
    {"id": "a", "metadata": {"doc_name": "D"}},
    {"id": "b", "metadata": {"doc_name": "D"}},
    {"id": "c", "metadata": {"doc_name": "D"}},
    {"id": "z", "metadata": {"doc_name": "OTHER"}},
]
assign_neighbors(chunks, window=2)
mb = chunks[1]["metadata"]
check("seq assigned in order", [c["metadata"]["seq"] for c in chunks[:3]] == [0, 1, 2])
check("prev_ids nearest-first", mb["prev_ids"] == ["a"])
check("next_ids nearest-first (window 2)", chunks[0]["metadata"]["next_ids"] == ["b", "c"])
check("neighbours don't cross documents", chunks[3]["metadata"]["prev_ids"] == [])

print("== BM25 uses bm25_text ==")
fillers = [
    {"id": "f1", "metadata": {"bm25_text": "penalty schedule and revocation terms",
                              "subsection_text": "penalty schedule and revocation terms"}},
    {"id": "f2", "metadata": {"bm25_text": "spectrum allocation and bandwidth planning",
                              "subsection_text": "spectrum allocation and bandwidth planning"}},
]
idx = BM25Index()
idx.build([c] + fillers)
res = idx.search("annual fee Licensee", top_k=3)
check("BM25 finds the chunk via subsection tokens",
      len(res) >= 1 and res[0]["subsection_text"] == SUB["subsection_text"])

print("== hierarchical_ops: multi-level filtering ==")
cands = [
    {"id": "1", "doc_name": "D1", "chapter": "C1", "section": "Licensing", "score": 0.9, "subsection_text": "x"},
    {"id": "2", "doc_name": "D1", "chapter": "C1", "section": "Licensing", "score": 0.7, "subsection_text": "y"},
    {"id": "3", "doc_name": "D1", "chapter": "C1", "section": "Penalties", "score": 0.6, "subsection_text": "z"},
    {"id": "4", "doc_name": "D1", "chapter": "C2", "section": "Misc", "score": 0.2, "subsection_text": "w"},
    {"id": "5", "doc_name": "D2", "chapter": "CX", "section": "Other", "score": 0.15, "subsection_text": "q"},
]
check("level_key qualifies section by parents",
      level_key(cands[0], "section") == ("D1", "C1", "Licensing"))
ranked = rank_groups(group_by(cands, "section"))
check("Licensing section ranks first", ranked[0][0][-1] == "Licensing")
out = apply_levels(
    [dict(c) for c in cands],
    levels=[{"field": "doc_name", "top_n": 1}, {"field": "chapter", "top_n": 1}, {"field": "section", "top_n": 1}],
)
kept = {c["section"] for c in out}
check("doc->chapter->section keeps only top path (Licensing)", kept == {"Licensing"})
check("base_score preserved before boost", all("base_score" in c for c in out))
check("section bonus boosts top score above raw", out[0]["score"] > out[0]["base_score"])

print("== hierarchical_ops: neighbour-expansion helpers ==")
check("classify high", classify_relevance(0.9, 0.65, 0.30) == "high")
check("classify low", classify_relevance(0.2, 0.65, 0.30) == "low")
check("classify medium", classify_relevance(0.5, 0.65, 0.30) == "medium")
check("select stops at first failure", select_passing_neighbors([0.8, 0.2, 0.9], 0.4) == 1)
check("cosine of identical vecs ~1", abs(cosine([1.0, 0.0], [1.0, 0.0]) - 1.0) < 1e-9)
check("cosine of orthogonal ~0", abs(cosine([1.0, 0.0], [0.0, 1.0])) < 1e-9)
check("build_continuation orders prev2,prev1,actual,next1",
      build_continuation("ACT", ["p1", "p2"], ["n1"]) == "p2\n\np1\n\nACT\n\nn1")

print("== HierarchicalRetriever: sibling + neighbour expansion ==")
from pipeline.stage3_retrieval.retrievers.hierarchical import HierarchicalRetriever


class FakeEmbedder:
    """Deterministic stand-in: query=[1,0]; neighbour p1 aligned, n1 orthogonal."""
    def initialize_db(self): pass
    def set_namespace(self, ns): pass
    def embed_query(self, q): return [1.0, 0.0]

    def search_by_vector(self, vec, top_k=5, filters=None):
        if filters:  # sibling expansion -> no extra siblings
            return {"matches": []}
        return {"matches": [{
            "id": "hit",
            "score": 0.50,  # medium -> triggers neighbour expansion
            "metadata": {
                "id": "hit", "doc_name": "D", "chapter": "C", "section": "S",
                "subsection_id": "2.0", "subsection_text": "ACTUAL",
                "prev_ids": ["p1"], "next_ids": ["n1"],
            },
        }]}

    def fetch_vectors(self, ids):
        table = {
            "p1": {"values": [1.0, 0.0], "metadata": {"subsection_text": "PREV1"}},
            "n1": {"values": [0.0, 1.0], "metadata": {"subsection_text": "NEXT1"}},
        }
        return {i: table[i] for i in ids if i in table}


retr = HierarchicalRetriever()
retr.set_embedder(FakeEmbedder())
results = retr.search("any query", top_k=10)
check("returns the hit", len(results) == 1)
hit = results[0]
check("medium hit flagged neighbour_expanded", hit.get("neighbor_expanded") is True)
check("aligned prev neighbour spliced in", "PREV1" in hit["subsection_text"])
check("orthogonal next neighbour NOT spliced", "NEXT1" not in hit["subsection_text"])
check("continuation keeps the actual chunk", "ACTUAL" in hit["subsection_text"])

print("== two-call gap analysis degrades gracefully ==")
gap = analyze_gap("some query", [{"subsection_text": "ctx", "doc_name": "D", "section": "S", "subsection_id": "1"}])
check("gap analysis returns GapAnalysis", isinstance(gap, GapAnalysis))
check("no-LLM -> treated as sufficient", gap.sufficient is True)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
