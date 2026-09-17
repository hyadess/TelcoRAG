"""Offline author workbench for the TelcoRAG pipeline (see DESIGN.md).

Importing this package pins the chunk store to the local knowledge base.

``.env`` carries the deployment's settings — ``TELCORAG_CHUNK_STORE=database``
and a Supabase ``DATABASE_URL`` — because the hosted feedback tool under
``tool/`` has no 336 MB knowledge base to read from. The author workbench does,
and it is offline by design: it must never depend on a database being reachable,
and a dead or rotated Supabase project must never stop an author from running a
query. ``LocalChunkStore`` and ``BM25Retriever`` both read this variable at
construction time, so pinning it here — before any pipeline module is imported —
covers both. ``load_dotenv()`` in the client modules does not override a value
that is already set, so ``.env`` cannot undo this.
"""

import os

os.environ["TELCORAG_CHUNK_STORE"] = "local"
