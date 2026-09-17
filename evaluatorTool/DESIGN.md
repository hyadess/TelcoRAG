# `evaluatorTool/` — design

**Status:** design document, first version.
**Written:** 2026-09-14.
**Scope:** a **deployed** rating application for the human evaluation. An admin creates evaluator accounts; each evaluator signs in and works through their assigned questions one at a time, rating a system answer against a reference answer and, on demand, the reference chunks with their source PDF pages.

---

## 0. How to read this document

Same marker convention as [`paper/guideline.md`](../paper/guideline.md) §0: **[VERIFIED]** / **[TO VERIFY]** / **[DECISION]** / **[SETTLED]**.

**Dependencies.** This tool is a *consumer*. [`humanEvaluation/DESIGN.md`](../humanEvaluation/DESIGN.md) is authoritative for the item-bank schema (§5.2 there), the assignment file schema (§6.2 there), and the rating instrument (§5.4 there). This document specifies only how those artifacts are served, collected against, and exported.

---

## 1. The hard constraint: do not touch `tool/`

**[SETTLED]** `tool/` is already deployed and must keep working unchanged. `evaluatorTool/` is a **separate application** with:

- its own folder, its own service, its own deployment;
- **its own database** — or at minimum its own schema and table names, so no migration can collide with `chat_responses`, `ratings`, `chunk_upload_tracker` or `chunk_artifacts` **[VERIFIED — `tool/backend/models.py`]**;
- its own environment prefix, `TELCORAG_EVAL_*`, so no variable name collides with `TELCORAG_RETRIEVER`, `TELCORAG_ADMIN_PASSWORD`, `TELCORAG_CHUNK_STORE` and the rest **[VERIFIED — `tool/settings.py`]**;
- **no shared Python modules with `tool/`.** Copy the few dozen lines that are genuinely common rather than importing across the boundary. An import is a coupling that will eventually force a change in `tool/`, and the constraint above forbids that.

`paper/guideline.md` §7.9 lists seven changes that would be needed to make `tool/` produce study-grade data — stable rater identity, condition recording, an ordered item queue, an extended rating schema, a pairwise table, export, and a locked dashboard. That is close to a rewrite. §7.9 then recommends the alternative taken here: **rate from frozen traces in a purpose-built app, and keep `tool/` for the deployment and exploratory story.**

Why frozen traces rather than live generation, restated because it is the design's foundation:

- every evaluator sees **byte-identical stimuli**;
- no latency, no API cost, and no non-determinism during rating sessions;
- the automatic judge scores **the same frozen outputs** the humans see — without which RQ2 is meaningless (`paper/guideline.md` §7.10);
- the deployed service needs **no** Pinecone, no Gemini, no Voyage, and no pipeline code. It is a form over a JSON file plus a PDF directory. That is a dramatically smaller thing to deploy and secure.

---

## 2. What the tool must do

1. **Admin creates evaluator accounts.** No self-signup, ever.
2. Each evaluator signs in and gets **their own** assigned questions, in **their own** fixed randomised order.
3. **One task per screen.** Left: the system answer. Right: the reference answer, plus a toggle revealing the reference chunks and their source PDF pages.
4. Collect the H1–H8 instrument, with **N/A** available and distinct on H1/H2.
5. Phase 2 pairwise, after Phase 1.
6. Export tidy long-format CSV for [`humanEvaluation/`](../humanEvaluation/DESIGN.md) §7.1.

### 2.1 Non-goals

- No chat, no free-text questions, no live retrieval.
- No scores visible to evaluators — not their own history, not anyone else's.
- No pipeline configuration UI. That is [`authorTool/`](../authorTool/DESIGN.md).

---

## 3. Stack

### 3.1 Decision

**[DECISION] FastAPI + Jinja2 server-rendered HTML, one service, one container.** Recommended over the alternatives.

| Option | Why not |
| --- | --- |
| Streamlit (as `tool/frontend`) | Multi-user auth is awkward and easy to get wrong; every widget interaction reruns the script, which fights a one-task-per-screen form; and a rerun mid-form is a data-loss path in a study you cannot re-run. |
| React SPA + FastAPI | Two build chains and a CORS surface for a UI that is a form, two panes and a PDF frame. |
| **FastAPI + Jinja2 + ~150 lines of vanilla JS** | Single deployable, no CORS, no build step, cookie sessions, and `<embed>`/`<iframe>` renders the PDF natively. |

The JS needed is genuinely small: the reference-chunk toggle, `←`/`→` page navigation, form-state guarding, and an autosave ping. No framework earns its weight here.

Note this is the **opposite** choice from [`authorTool/`](../authorTool/DESIGN.md) §3.1, deliberately. That tool is offline, single-user, and calls the pipeline in-process, so Streamlit is ideal. This one is deployed, multi-user, authenticated, and serves static artifacts — different problem, different tool.

### 3.2 Folder layout

```
evaluatorTool/
├── README.md
├── DESIGN.md                   # this file
├── requirements.txt
├── Dockerfile
├── docker-compose.yml          # local: app + postgres
├── settings.py                 # TELCORAG_EVAL_* only
├── backend/
│   ├── main.py                 # FastAPI app, routes
│   ├── database.py
│   ├── models.py               # SQLAlchemy (§5)
│   ├── schemas.py              # Pydantic (§6)
│   ├── auth.py                 # password hashing, sessions, dependencies
│   ├── bank.py                 # loads + validates item_bank.json; opaque tokens
│   ├── pages.py                # PDF streaming, path validation (§8)
│   ├── admin.py                # account creation, progress, flags
│   └── export.py               # tidy long CSV (§10)
├── templates/
│   ├── base.html  login.html  task.html  pairwise.html
│   ├── done.html  admin.html
│   └── partials/_chunk.html  _rubric.html
├── static/
│   ├── app.css
│   └── app.js
├── data/                       # mounted from the frozen build; read-only
│   ├── item_bank.json
│   ├── item_bank.sha256
│   └── assignments/E01.json … N06.json
└── pages/                      # pruned page PDFs (§8.2); read-only
    └── ISP/page_16.pdf …
```

`data/` and `pages/` are **generated by [`humanEvaluation/`](../humanEvaluation/DESIGN.md) and mounted read-only.** The application must never write into either.

---

## 4. Accounts and authentication

### 4.1 Admin-created accounts only

**[SETTLED]** There is **no public signup route.** Not disabled — absent. An account is created by the admin, who sets the evaluator code, tier, set, and an initial password.

Rationale: the evaluator roster is fixed at 12 by the design (`humanEvaluation/DESIGN.md` §3.5), codes must match assignment files exactly, and tier and set are study variables rather than user preferences. A self-signup route could only introduce a rater whose data cannot be analysed.

**Evaluator record:** `code` (`E01`–`E06`, `N01`–`N06`), `tier` (`expert` \| `non_expert`), `set` (`A` \| `B`), password hash, `consent_at`, `active`, `created_at`, `created_by`.

**Validation at creation:** the code must match an assignment file in `data/assignments/`, and its `tier` and `set` must match that file's. A mismatch between roster and assignment is silent data corruption otherwise — an evaluator would receive the wrong set.

This closes **G7** from `paper/guideline.md` §6: `tool/frontend/app.py` assigns `rater_id = uuid.uuid4().hex` per browser session **[VERIFIED]**, so a page reload creates a phantom rater and inter-rater reliability is uncomputable. Here, identity is an account.

### 4.2 Sessions

- **Argon2id** (or bcrypt) password hashing. Never store plaintext.
- Server-side session, HttpOnly + Secure + SameSite=Lax cookie. 12-hour idle expiry — long enough for a rating session of up to 18 tasks, short enough to matter.
- Forced password change on first login.
- **Consent gate:** an evaluator who has not accepted the consent text cannot reach a task. `consent_at` is stamped on acceptance, and the consent version is recorded — `paper/guideline.md` §7.13 makes written informed consent non-negotiable, and the timestamp is the record.
- Rate-limit login attempts.
- Admin is a separate role on the same table, or a single account from `TELCORAG_EVAL_ADMIN_PASSWORD`. **[DECISION]** A separate `admins` table is cleaner; a single env-var admin is acceptable for a 12-user study. Either way it must **not** reuse `TELCORAG_ADMIN_PASSWORD`, which belongs to `tool/`.

---

## 5. Data model

New tables, prefixed `eval_` so they cannot collide with `tool/`'s.

```
eval_evaluators
    id, code (unique), tier, set, password_hash, must_change_password,
    consent_at, consent_version, active, created_at, created_by

eval_sessions
    id, evaluator_id, token_hash, created_at, expires_at, ip_hash, user_agent

eval_assignments
    id, evaluator_id, phase (1|2), position, session_no,
    item_id,           -- phase 1; opaque to the client (§7.5)
    question_id,       -- phase 2
    left_condition, right_condition,   -- phase 2, recorded for un-blinding
    is_catch, bank_sha256
    UNIQUE (evaluator_id, phase, position)

eval_ratings                      -- phase 1
    id, assignment_id (unique), evaluator_id, item_id,
    h1_retrieval_relevance      INT NULL,   h1_na BOOL,
    h2_groundedness             INT NULL,   h2_na BOOL,
    h2_unsupported_quote        TEXT,
    h3_completeness             INT NOT NULL,
    h4_correctness              INT NOT NULL,
    h5_decision_usability       INT NOT NULL,
    h6_abstention               VARCHAR(32),
    h7_failure_tags             JSON,
    h8_comment                  TEXT,
    started_at, submitted_at, duration_ms,
    reference_revealed BOOL, reference_revealed_at,
    chunks_opened BOOL, chunk_views JSON, pdf_pages_viewed JSON,
    bank_sha256, created_at, updated_at

eval_pairwise                     -- phase 2
    id, assignment_id (unique), evaluator_id, question_id,
    left_condition, right_condition,
    choice VARCHAR(8),            -- 'left' | 'right' | 'tie'
    reason TEXT, started_at, submitted_at, duration_ms

eval_events                       -- append-only telemetry
    id, evaluator_id, assignment_id, event_type, payload JSON, created_at
```

Five things this schema gets right that a naive one would not:

1. **`h1`/`h2` are NULL-able with an explicit `*_na` flag.** `paper/guideline.md` §7.4.2: H1 and H2 are *undefined* on C1, and "coding an undefined item as the lowest score manufactures an enormous artificial condition effect and poisons every mean, every reliability coefficient and every model fit." A NULL plus a flag distinguishes *not applicable* from *not answered* — and only the flag makes that distinction auditable. `tool/backend/models.py` makes `retrieval_relevance` a non-null `Integer` **[VERIFIED]**, which is exactly the trap being avoided.
2. **`bank_sha256` on every rating row.** If the item bank is ever re-frozen, ratings against the old hash are detectable rather than silently pooled.
3. **`left_condition`/`right_condition` stored server-side** for Phase 2, so randomised A/B can be un-blinded at analysis time — the human analogue of the position swap in `evaluation/judge/modules/pairwise.py` **[VERIFIED]**.
4. **`reference_revealed` telemetry** — see §7, where it earns its place.
5. **`UNIQUE (assignment_id)` on ratings.** One rating per assigned task, revisable. This is the meaningful version of the `(response_id, rater_id)` constraint already in `tool/` **[VERIFIED]**, which is undermined there by unstable rater ids.

---

## 6. Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Redirect to next task, or to login |
| `GET`/`POST` | `/login` · `/logout` · `/password` · `/consent` | Auth and consent gate |
| `GET` | `/task` | Next unrated assignment (§7) |
| `GET` | `/task/{position}` | A specific task; revisable while the phase is open |
| `POST` | `/task/{position}` | Submit a rating |
| `POST` | `/task/{position}/autosave` | Draft save (§7.6) |
| `POST` | `/task/{position}/event` | Telemetry: reference revealed, chunk opened, page viewed |
| `GET` | `/pairwise` · `/pairwise/{position}` · `POST /pairwise/{position}` | Phase 2 |
| `GET` | `/pages/{doc_folder}/{page}.pdf` | **Authenticated PDF page stream (§8)** |
| `GET` | `/progress` | The evaluator's own completion count — **no scores** |
| `GET` | `/done` | End-of-phase screen |
| `GET`/`POST` | `/admin/…` | Accounts, progress, flags, export (§9) |
| `GET` | `/health` · `/health/db` | Liveness, matching `tool/`'s convention **[VERIFIED]** |

---

## 7. The rating screen

### 7.1 Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Task 7 of 45            Session 1            [Rubric ▾]      E01       │
├─────────────────────────────────────────────────────────────────────────┤
│  QUESTION                                                               │
│  What are the requirements for lawful interception (LI) for ISP?        │
├──────────────────────────────────┬──────────────────────────────────────┤
│  ANSWER                          │  REFERENCE ANSWER                    │
│                                  │  Under clause 30.1, an ISP licensee  │
│  The licensee shall provide      │  shall …                             │
│  lawful interception capability  │                                      │
│  at its own cost …               │  ┌────────────────────────────────┐  │
│                                  │  │ [ Show reference chunks (12) ] │  │
│                                  │  └────────────────────────────────┘  │
├──────────────────────────────────┴──────────────────────────────────────┤
│  H1 Retrieval relevance    (1)(2)(3)(4)(5)   [N/A]                      │
│  H2 Groundedness           (1)(2)(3)(4)(5)   [N/A]                      │
│     ↳ Quote the unsupported statement: ____________  (required if ≤4)   │
│  H3 Completeness           (1)(2)(3)(4)(5)                              │
│  H4 Correctness            (1)(2)(3)(4)(5)                              │
│  H5 Decision usability     (1)(2)(3)(4)(5)                              │
│  H6 Abstention   ( ) correct  ( ) over  ( ) confabulation  ( ) n/a      │
│  H7 Failure tags  [ ] wrong_fee_or_amount  [ ] dropped_condition …      │
│  H8 Comment  ______________________________________________            │
│                                              [ Save and continue → ]    │
└─────────────────────────────────────────────────────────────────────────┘
```

Anchors are **always on screen**, not in a briefing document — `paper/guideline.md` §7.8 step 1. Every radio shows its anchor text on hover or beneath, and the `[Rubric ▾]` panel holds the full wording. Unanchored 1–5 sliders are the single biggest source of noise in human evaluation, and the current `tool/` has none beyond "1 (poor) to 5 (excellent)" **[VERIFIED]**.

### 7.2 The reference-chunk overlay

`[ Show reference chunks ]` opens a full-width overlay:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Chunk 3 of 12  ·  ISP  ·  page 16 of 47  ·  deck 7 of 19        [ ✕ ]  │
├────────────────────────────────────┬────────────────────────────────────┤
│  §30. CHANGES IN OWNERSHIP         │                                    │
│  subsection 30.1 · pages 16        │        [ PDF page 16 ]             │
│                                    │                                    │
│  The licensee shall not, without   │                                    │
│  prior written approval …          │                                    │
├────────────────────────────────────┴────────────────────────────────────┤
│   [← Previous page]   ( 1 )( 2 )(3)( 4 ) … chunk jump   [Next page →]   │
└─────────────────────────────────────────────────────────────────────────┘
```

**The navigation model is the flattened page deck**, identical to [`authorTool/DESIGN.md`](../authorTool/DESIGN.md) §5.4 — deliberately, so the two tools behave the same way and only one model has to be explained to anyone:

```
deck = [ (chunk_rank, doc_folder, page_no) ]
       for each chunk in rank order, for each page in that chunk's sorted list
```

- `←` / `→` step one position through the deck, crossing chunk boundaries. **Disabled at the ends — no wrapping.**
- A chunk-number strip jumps to the first page of that chunk.
- Breadcrumb always visible, with both denominators: position in the document *and* position in the evidence.
- Keyboard `←`/`→` bound directly — trivial here, since this is real HTML rather than Streamlit.

`page_numbers` arrives from the bank **already parsed into a list of ints** (`humanEvaluation/DESIGN.md` §5.2). The client must not re-parse comma strings, and must not expand a span into a contiguous range — one NFAP chunk spans 57 **non-contiguous** pages **[VERIFIED]**, and filling the gaps would fabricate provenance.

### 7.3 C1 — the no-retrieval condition

C1 items carry `chunks: []`. The screen must then:

- **hide** the `[ Show reference chunks ]` button — showing an empty overlay invites the evaluator to record a low H1 for "nothing there";
- render H1 and H2 as **N/A, pre-selected and locked**, with a one-line explanation: *"No source passages were shown for this answer, so these two items do not apply."*;
- keep H3, H4, H5, H6, H7, H8 fully active. **H6 is the point of C1** — it is where confabulation on the T6 stratum is measured.

### 7.4 Conditional fields

- **H2 follow-up:** when H2 ≤ 4, *"Quote the unsupported statement"* is **required**. This produces machine-comparable evidence against the judge's `hallucinated_claims` field **[VERIFIED — `core/schemas.py`]**.
- **H7 and H8:** shown when any of H2–H5 ≤ 3; H8 required in that case, optional otherwise.
- **H6** is shown on every item but only *analysed* on the T6 stratum.
- H7 tag list, seeded from `paper/guideline.md` §7.6 and extensible after the pilot:
  `wrong_licence_category` · `wrong_fee_or_amount` · `dropped_condition_or_exception` · `outdated_or_superseded_provision` · `conflated_two_documents` · `missing_part_of_list` · `right_document_wrong_section` · `vague_non_answer` · `contradicts_itself` · `other (specify)`

### 7.5 Blinding

From `paper/guideline.md` §7.7, enforced in code rather than by convention:

- **The condition is never sent to the client.** Not in HTML, not in JSON, not in a URL, not in a `data-` attribute, not in a CSS class.
- **`item_id` is never sent either.** `Q07-C3` leaks the condition in its own name. The server issues an **opaque per-evaluator token** — e.g. `HMAC(server_secret, evaluator_id || item_id)`, truncated — and resolves it back server-side. Assignment positions are addressed by `position`, which leaks nothing.
- No model names, retriever names, or configuration anywhere in the evaluator-facing UI.
- Evaluators cannot see other evaluators' ratings, or aggregate statistics, or their own past scores. `/progress` returns a completion count only.
- Evaluator-facing materials should never mention that the team built any of the systems.

### 7.6 Robustness

These matter because a lost rating cannot be recovered — the evaluator has already read the item and cannot un-read it.

- **Autosave the draft** on every field change, debounced. A closed laptop must not cost a rating.
- **Resume** at the first unrated position on login.
- **Revisable within the open phase**, then locked when the phase closes.
- **`beforeunload` guard** on a dirty form.
- **Server-side validation mirrors the client's.** Required-when rules are study rules, not UI conveniences, and a client can always be bypassed.
- **Timestamps** `started_at` / `submitted_at` / `duration_ms` per task — needed to report median time-on-item and to check for speeding (`paper/guideline.md` §7.8 step 4), and to settle the **[TO VERIFY]** 4 min/task estimate.

### 7.7 The reference answer is visible — a deliberate deviation, and what it costs

**[DECISION — team's, recorded here with its consequences.]**

`paper/guideline.md` §7.6 states: *"Do not show the reference answer for items H1–H4."* This design shows it for every item, in the right pane. That is the team's call and it is implementable, but the manuscript must handle three consequences — and it is much better to state them than to have a reviewer find them.

1. **H4 becomes reference-aided correctness for both tiers.** §7.6 of the guideline recommends unaided for experts and aided for non-experts, and notes that the difference is itself an RQ4 finding. Showing it to everyone forgoes that finding and makes H4 a *conformance-to-reference* measure rather than an *unaided-usefulness* measure. **Describe it as reference-aided correctness in the Method. Never describe H4 as unaided.**
2. **Anchoring risk on H3 and H5.** A visible reference answer defines what "complete" looks like, so H3 measures agreement with the reference's scope, and H5 may be judged against the reference rather than against the evaluator's own practice.
3. **It raises measured agreement with the LLM judge.** `answer_correctness` is itself reference-conditioned **[VERIFIED — it is the one judge module that requires a reference]**. Aiding the human with the same reference pushes both toward the same target, which **inflates the RQ2 agreement statistic** — and RQ2 is the paper's contribution. This is the consequence that actually threatens the central claim.

**Mitigation, and it is cheap:** make the reference **collapsed by default**, revealed by a click, and record `reference_revealed` plus `reference_revealed_at`.

That single change buys three things. Evaluators who form a judgement before revealing produce a partially unaided H4. The reveal rate becomes a reportable behavioural measure — *how often does an expert feel the need to check?* — which is a genuinely interesting datum for this venue. And §7.4 of [`humanEvaluation/DESIGN.md`](../humanEvaluation/DESIGN.md) can compute the RQ2 agreement statistic **split by whether the reference was revealed**, which converts consequence 3 from an uncontrolled confound into a measured moderator.

**Recommendation: collapsed by default, reveal logged.** The visual design in §7.1 already accommodates this — the right pane shows the reference-answer heading with a reveal control, and the chunk toggle sits beneath it.

---

## 8. Serving PDFs

**[SETTLED]** The backend streams page PDFs from its own filesystem.

### 8.1 Endpoint

```
GET /pages/{doc_folder}/{page}.pdf        → 200 application/pdf
```

Validation, in this order, with no shortcuts:

1. **Authenticated.** An unauthenticated request gets 401, never a file. The corpus is public, but an open file endpoint on a study server is an unnecessary liability.
2. **`doc_folder` must match `^[A-Za-z0-9_]+$`** *and* be a key in the folder whitelist built from the item bank at startup. Never `os.path.join` untrusted input — this is the path-traversal surface, and `..%2f` is the first thing anyone tries.
3. **`page` must parse as an integer** and be in the page whitelist for that folder, also derived from the bank. A page no item cites is not served.
4. Resolve to an absolute path, then **assert the resolved path is inside the pages root** — belt and braces against symlinks.
5. Serve with `Cache-Control: private, max-age=86400` and an `ETag`. Pages are immutable for the study's life, so this makes navigation feel instant after first view.

The whitelist in steps 2–4 is derived from data, not configuration, so it cannot drift from the item bank.

### 8.2 What goes on disk

**[DECISION] Ship only the pages the frozen item bank cites.** `humanEvaluation/scripts/05_freeze.py` walks every chunk of every item, collects `(doc_folder, page)` pairs, and copies just those into `evaluatorTool/pages/`.

For scale: the full corpus is **1,172 page PDFs totalling 261 MB [VERIFIED]**, and `knowledge_base/` overall is 336 MB. A 72-item bank whose chunks are capped at `rerank_top_k: 20` **[VERIFIED]** will cite far fewer distinct pages than that — though **[TO VERIFY]** the exact figure, since one NFAP chunk alone spans 57 pages and a handful of such chunks would dominate the count. Compute it at freeze time and record it.

Why prune rather than mount the whole corpus:

- the deploy artifact stays small, so the service starts fast and is cheap to host;
- the served set is **exactly** the evidence the study froze — the whitelist and the bank cannot disagree;
- it removes any chance of an evaluator reaching a document outside their item's evidence.

**Fallback if pruning proves awkward:** mount the full 261 MB. It still fits a small persistent disk. The whitelist in §8.1 stays derived from the bank regardless, so pruning is a deployment optimisation, not a security control.

### 8.3 Rendering

`<embed type="application/pdf">` (or `<iframe>`) pointed at the endpoint. The browser's own PDF viewer handles rendering, and it is better than anything worth building. Provide a fallback link for browsers that do not render PDFs inline, and `/pages/{folder}/{page}.md` serving `markdowns/page_N.md` as a text alternative.

---

## 9. Admin

- **Create evaluator** — code, tier, set, initial password; validated against the assignment files (§4.1).
- **Deactivate** / reset password.
- **Progress** — per evaluator: tasks completed, current session, median duration, last activity. **No scores.**
- **Catch-item flags** — evaluators who scored a catch item ≥ 4 on H4 (`humanEvaluation/DESIGN.md` §5.5). Surface the flag; the pre-specified exclusion rule is applied at analysis time, not in the app.
- **Bank status** — loaded hash, item count, assignment count, and any mismatch between a rating's `bank_sha256` and the loaded bank.
- **Export** (§10).
- **Phase control** — open/close Phase 1 and Phase 2, locking submissions.

**Lock the dashboard during collection.** `paper/guideline.md` §7.7 requires that raters cannot see others' scores, and §7.9(g) notes that `tool/`'s analytics endpoint is *intentionally open when `TELCORAG_ADMIN_PASSWORD` is empty* **[VERIFIED — `tool/README.md`]**. Do not repeat that here: `TELCORAG_EVAL_ADMIN_PASSWORD` must be **required at startup** — the app should refuse to boot without it, rather than defaulting to open.

---

## 10. Export

`GET /admin/export.csv` produces the tidy long format `humanEvaluation/` §7.1 expects — **one row per (evaluator, item, criterion)**:

```
evaluator_code, tier, set, item_id, question_id, type, answerable,
condition, criterion, value, is_na, comment, failure_tags,
unsupported_quote, reference_revealed, duration_ms, submitted_at, bank_sha256
```

Plus `export_pairwise.csv`:

```
evaluator_code, tier, set, question_id, left_condition, right_condition,
choice, choice_condition, reason, duration_ms, submitted_at
```

`choice_condition` resolves `left`/`right`/`tie` to the actual condition — the un-blinding, done once, server-side, so no analysis script has to re-derive it and get it wrong.

Rules:

- `condition` and `item_id` appear **in the export only**, never in an evaluator-facing response.
- Catch items are exported with `is_catch = true` rather than dropped, so the flag rate is auditable.
- N/A rows carry `is_na = true` and an **empty** `value` — never `0`, never `1`.
- Export includes the bank hash in a header comment and as a column.

---

## 11. Deployment

### 11.1 `tool/`'s deployment path does not work here

**[VERIFIED]** `tool/deploy.md` deploys the FastAPI backend to **Vercel**, with the Streamlit UI on Streamlit Community Cloud, chunks in Supabase, and vectors in Pinecone.

**That path cannot serve this tool's PDFs.** Vercel functions are serverless with an ephemeral, size-capped filesystem; 261 MB of page PDFs on a persistent disk is exactly what they do not provide. The team has chosen disk-based serving (§8), so **`evaluatorTool/` needs a host with a persistent volume.**

This is the most consequential operational difference between the two tools, and it should be settled before anyone starts building.

### 11.2 Target

**[DECISION] A container host with a persistent volume** — Render, Railway, Fly.io, or a small VPS.

| Component | Choice |
| --- | --- |
| App | One container: FastAPI + Uvicorn, Jinja templates, static files |
| Database | Managed Postgres. **Supabase is fine** — it is only Postgres here, and a **separate database or schema** from `tool/`'s (§1) |
| PDFs + bank | Persistent volume mounted read-only at `/data` and `/pages` |
| TLS | Provided by the host |

**Sizing:** ≤ 1 GB disk, 512 MB RAM, 1 vCPU. There is no model inference, no vector search, and no pipeline code in this service — it serves JSON and static PDFs to at most 12 concurrent users. Right-size it and spend the attention elsewhere.

### 11.3 Environment

```dotenv
TELCORAG_EVAL_DATABASE_URL=postgresql+psycopg://…
TELCORAG_EVAL_SECRET_KEY=…            # session + opaque item tokens
TELCORAG_EVAL_ADMIN_PASSWORD=…        # required; app refuses to start without it
TELCORAG_EVAL_BANK_PATH=/data/item_bank.json
TELCORAG_EVAL_BANK_SHA256=…           # asserted at startup
TELCORAG_EVAL_ASSIGNMENTS_DIR=/data/assignments
TELCORAG_EVAL_PAGES_ROOT=/pages
TELCORAG_EVAL_PHASE=1                 # 1 | 2 | closed
```

Every name carries the `TELCORAG_EVAL_` prefix so nothing collides with `tool/settings.py` **[VERIFIED]**.

### 11.4 Startup assertions — fail loudly, not quietly

The app must refuse to start if any of these fails. Each one, undetected, corrupts data that cannot be re-collected.

1. Bank file loads and its sha256 matches `TELCORAG_EVAL_BANK_SHA256`.
2. Every `item_id` in every assignment file exists in the bank.
3. Every `(doc_folder, page)` cited by any item exists under `TELCORAG_EVAL_PAGES_ROOT`.
4. Every evaluator account's `tier` and `set` match its assignment file.
5. `TELCORAG_EVAL_ADMIN_PASSWORD` and `TELCORAG_EVAL_SECRET_KEY` are non-empty.
6. Every C1 item has `chunks == []`, and every C2/C3 item has at least one chunk.

A study app that boots into a broken state collects bad data silently for hours. A study app that refuses to boot costs ten minutes.

### 11.5 Backups

Back up the database **nightly and after every session**. The rating table is irreplaceable: an evaluator cannot re-rate an item they have already seen without contaminating the judgement. This is the highest-value, lowest-effort safeguard in the whole project.

---

## 12. Build order

| # | Step | Gives you |
| --- | --- | --- |
| 1 | Skeleton, settings, DB, models, migrations | Deployable shell |
| 2 | `bank.py`: load, validate, startup assertions (§11.4), opaque tokens | Blinding + integrity |
| 3 | Auth: admin-created accounts, sessions, consent gate | Identity (closes **G7**) |
| 4 | `pages.py`: PDF endpoint with full path validation (§8.1) | The hard dependency for the overlay |
| 5 | `task.html`: two panes, instrument, conditional fields, N/A locking | **The core screen** |
| 6 | The chunk overlay: deck, `←`/`→`, breadcrumb, keyboard | The evidence view |
| 7 | Autosave, resume, timestamps, telemetry events | Robustness + reveal data |
| 8 | Phase 2 pairwise | RQ2 preference agreement |
| 9 | Admin: progress, flags, phase control | Running the study |
| 10 | Export (§10) | Hands off to `humanEvaluation/` |
| 11 | Deploy + pilot with 2 evaluators | Timing data; settles the 4 min/task **[TO VERIFY]** |

Step 4 before step 5 because the overlay is the riskiest piece and the one most likely to need rework.

---

## 13. Open decisions

| # | Decision | Recommendation |
| --- | --- | --- |
| D1 | Reference answer visible by default? (§7.7) | **Collapsed by default, reveal logged.** Preserves a partially-unaided H4 and turns the confound into a measured moderator |
| D2 | Prune pages, or mount the whole 261 MB? (§8.2) | Prune at freeze time; whitelist stays bank-derived either way |
| D3 | Admin as a table row or a single env-var account? (§4.2) | Either; a table is cleaner, env-var is acceptable at 12 users |
| D4 | Separate database, or a separate schema in `tool/`'s? (§1) | **Separate database.** Cheap, and removes the collision question entirely |
| D5 | Host | Any container host with a persistent volume. **Not Vercel** (§11.1) |
| D6 | Markdown page fallback alongside the PDF? (§8.3) | Yes — nearly free, and it is the accessibility path |
