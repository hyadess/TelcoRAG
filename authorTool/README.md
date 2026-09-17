# `authorTool/`

An **offline** workbench for authors: run the TelcoRAG pipeline under any configuration, ask a question, read the answer, and inspect the exact evidence behind it — retrieved chunks side by side with their source PDF pages, navigable with `←` / `→` in a page overlay.

```bash
pip install -r requirements.txt -r authorTool/requirements.txt
streamlit run authorTool/app.py --server.address=127.0.0.1
```

| Path | What it is |
| --- | --- |
| [`DESIGN.md`](DESIGN.md) | The full design: architecture, the registry-driven configuration surface, the document index, the page-deck overlay, comparison mode, and the decisions behind each. |
| `app.py` | Entrypoint. Four tabs: **Ask**, **Compare**, **Knowledge base**, **Saved runs**. |
| `library.py` | The Knowledge base tab: any ingested document by page and by chunk, plus a literal search over the whole corpus. |
| `evidence.py` | `doc_name` → folder, `page_numbers` → page files. Builds and caches the document index. |
| `viewer.py` | The evidence overlay: chunk text beside the PDF page, flattened `(chunk, page)` deck. |
| `config_panel.py` / `config_resolver.py` | The sidebar form, and the `pipeline.yaml` → overrides → effective-config merge. |
| `runner.py` | Builds the pipeline (cached by config hash), runs a query, records the trace. |
| `compare.py` | One question, one configuration key varied, columns side by side. |

Three properties this tool must keep:

- **Offline and unauthenticated.** It reads the local 336 MB `knowledge_base/` with the author's own API keys. Never deploy it; bind it to `127.0.0.1`.
- **It talks to no database.** `authorTool/__init__.py` pins `TELCORAG_CHUNK_STORE=local`, so the Supabase `DATABASE_URL` in `.env` — which exists for the deployed `tool/` app, whose host has no knowledge base to read — is ignored here. An unreachable, rotated or deleted Supabase project cannot stop an author from running a query.
- **It never writes `config/pipeline.yaml`.** UI configuration is an overlay over the YAML, never a mutation of it.
- **It enumerates plugins from `core/registry.py` at runtime**, so a new retriever or embedder appears with zero edits here.

**No presets, no named conditions.** A configuration is any combination of the keys in `config/pipeline.yaml`, identified by the `sha256` of the effective config — shown next to every answer and written into every saved run. Condition definitions (C1/C2/C3) belong to [`humanEvaluation/`](../humanEvaluation/DESIGN.md) and `paper/guideline.md`, not here. See `DESIGN.md` §4.5.

**Saved runs cost nothing.** The last tab opens any `data/runs/*.json` in the same evidence viewer with no API calls, so provenance reading never depends on re-running the pipeline. Saving a run is an explicit button and writes one local JSON file — the only thing this tool persists.

**The corpus is readable without retrieval.** The Knowledge base tab opens any of the 25 ingested documents directly — page PDFs, the parsed markdown that was actually chunked, every chunk with its metadata, and a literal substring search across all 6,858 chunks. That search is the control for the question retrieval cannot answer: *did retrieval miss it, or is it simply not in the corpus?*

Related: [`humanEvaluation/`](../humanEvaluation/DESIGN.md) (this tool helps author the question pool and capture gold provenance) · [`evaluatorTool/`](../evaluatorTool/DESIGN.md) (shares the page-deck navigation model) · [`paper/guideline.md`](../paper/guideline.md).

Facts in `DESIGN.md` are marked **[VERIFIED]** or **[DECISION]**. The one **[TO VERIFY]** that blocked the build is settled: page-number alignment holds across all 25 documents, and no document needs a page offset (§2.4).
