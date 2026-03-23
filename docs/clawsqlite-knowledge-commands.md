# Knowledge CLI Commands (Current `clawsqlite knowledge` surface)

This document inventories the existing `clawsqlite knowledge` CLI commands and classifies
them as:

- **Plumbing wrapper candidate** – can/should be re-expressed using
  `clawsqlite db/index/fs` primitives, and exposed as `clawsqlite
  knowledge ...` wrappers.
- **Application-level** – knowledge-specific behavior that should stay in
  the `knowledge` namespace (and may internally use plumbing commands).

## 1. Command inventory

> NOTE: This section describes the CLI surface as implemented in
> `clawsqlite_knowledge/cli.py`. These commands are exposed to
> users/skills under the namespace:
>
> ```bash
> clawsqlite knowledge ingest
> clawsqlite knowledge search
> ...
> ```

Source: `clawsqlite_knowledge/cli.py`.

Additional notes (current behavior):

- `clawsqlite knowledge ...` auto-loads a project-level `.env` from the current working directory (does not override existing env vars).
- When embeddings are not available:
  - `search --mode hybrid` falls back to FTS-only and prints a `NEXT:` hint.
  - `search --mode vec` returns an error and prints a `NEXT:` hint.

### 1.1 `ingest`

**CLI:**

```bash
clawsqlite knowledge ingest --url ...
clawsqlite knowledge ingest --text ...
```

**Description:**

- Fetches content from a URL (or takes raw text),
- optionally calls a generator to produce title/summary/tags,
- inserts a new article row into the DB (or updates an existing one),
- writes a Markdown file to `articles_dir`,
- syncs FTS and vector indexes for the new/updated article.

**Classification:**

- **Application-level (knowledge)** – this is a full business workflow
  (scrape + LLM + markdown + DB + index). It should remain under
  `clawsqlite knowledge ingest` and **not** be turned into a plumbing
  primitive.

---

### 1.2 `search`

**CLI:**

```bash
clawsqlite knowledge search "query" [--mode hybrid|fts|vec] [--category ...] [...]
```

**Description:**

- Opens the DB with FTS + vec enabled;
- Determines embedding availability (required env + vec0/vec table readiness):
  - if `--mode vec` and embeddings are unavailable: exits non-zero and prints `NEXT:` guidance;
  - if `--mode hybrid` and embeddings are unavailable: prints a `NEXT:` hint and falls back to FTS-only;
- Calls `hybrid_search(...)` with:
  - query text;
  - search mode (hybrid/fts/vec);
  - topk/candidates parameters;
  - filters: category, tag, since, priority, include_deleted;
  - optional keyword expansion via LLM (llm-keywords).
- Prints either JSON or a human-readable table of results.

**Classification:**

- **Application-level (knowledge)** – uses KB-specific filters and output
  formatting.
- **May internally use plumbing**:
  - future `clawsqlite index search` could be used as a core primitive for
    the ranking step;
  - but the filtering and presentation logic belongs in
    `clawsqlite knowledge search`.

---

### 1.3 `show`

**CLI:**

```bash
clawsqlite knowledge show --id 123 [--full]
```

**Description:**

- Loads a single article by ID from the DB;
- Optionally reads the Markdown file and includes full content when
  `--full` is set;
- Prints either JSON or a formatted text block.

**Classification:**

- **Application-level (knowledge)** – concept of an "article" with
  metadata + markdown content is KB-specific.
- Internally uses DB and filesystem, but the semantics are not generic
  enough for plumbing.

---

### 1.4 `export`

**CLI:**

```bash
clawsqlite knowledge export --id 123 --format md|json --out path [--full]
```

**Description:**

- Loads an article by ID;
- Reads the Markdown file if present;
- Writes either:
  - a JSON file with metadata (and optional full content), or
  - a Markdown file with a METADATA/SUMMARY header (or the full markdown
    when `--full`).

**Classification:**

- **Application-level (knowledge)** – export format and semantics are KB
  specific.
- Plumbing may provide file/DB primitives, but the export command itself
  stays under `knowledge`.

---

### 1.5 `update`

**CLI:**

```bash
clawsqlite knowledge update --id 123 [--title ...] [--summary ...] [--tags ...] \
  [--category ...] [--priority ...] [--regen ...]
```

**Description:**

- Loads an article by ID;
- Applies patch fields: title/summary/tags/category/priority；
- Optionally regens fields via generator (`--regen title|summary|tags|all`);
- Updates DB row;
- Syncs FTS index for this article;
- Syncs vec index when embeddings are enabled and either:
  - the summary changed, or
  - `--regen embedding` / `--regen all` was explicitly requested.
- For `regen` it may read the markdown file as the content source.

**Classification:**

- **Application-level (knowledge)** – patch/regen semantics are fully KB
  specific.
- Internally uses DB/FTS/vec, but should remain as
  `clawsqlite knowledge update`.

---

### 1.6 `delete`

**CLI:**

```bash
clawsqlite knowledge delete --id 123 [--hard] [--remove-file]
```

**Description:**

- Soft delete (default):
  - renames the markdown file to `.bak_deleted_<timestamp>`;
  - sets `deleted_at` in the DB;
  - removes FTS/vec entries.
- Hard delete (`--hard`):
  - removes FTS/vec entries;
  - deletes the DB row;
  - either removes the file or renames it to a `.bak_deleted_...` file
    depending on `--remove-file`.

**Classification:**

- **Application-level (knowledge)** – the soft/hard delete semantics and
  `.bak_deleted_` convention are KB-specific.
- Internally touches DB/FTS/vec/filesystem, but remains under
  `clawsqlite knowledge delete`.

---

### 1.7 `reindex`

**CLI:**

```bash
clawsqlite knowledge reindex --check | --fix-missing | --rebuild [--fts] [--vec]
```

**Description:**

- Opens DB with FTS + vec;
- Depending on flags:
  - `--check`:
    - calls `reindex_mod.check(...)` to inspect index status and missing
      fields;
  - `--fix-missing`:
    - calls `reindex_mod.fix_missing(...)` to fill missing fields and
      index rows (may invoke generator/embedding);
  - `--rebuild`:
    - for `--fts`: the knowledge CLI typically delegates to plumbing (`clawsqlite index rebuild`) to rebuild FTS;
    - for `--vec`: clears the vec table only (does **not** recompute embeddings).

**Classification:**

- Mixed:
  - `--rebuild --fts/--vec` is a **plumbing wrapper candidate** → should be
    refactored to call `clawsqlite index check/rebuild` with fixed
    `--table` / `--id-col` / `--fts-table` / `--vec-table`.
  - `--check` / `--fix-missing` involve KB-specific field generation and
    are **application-level**.

---

### 1.8 `embed-from-summary`

**CLI:**

```bash
clawsqlite knowledge embed-from-summary [--where ...] [--limit ...] [--offset ...]
```

**Description:**

- Knowledge-level wrapper around the plumbing embedding primitive (`clawsqlite embed column`);
- Uses the default KB schema:
  - base table: `articles`
  - id column: `id`
  - text column: `summary`
  - vec table: `articles_vec`
  - default WHERE: `deleted_at IS NULL AND summary IS NOT NULL AND trim(summary) != ''`
- Supports `--where/--limit/--offset` for batching.

**Classification:**

- **Plumbing wrapper candidate** – thin knowledge wrapper around a generic embedding primitive.

---

### 1.9 `maintenance`

**CLI:**

```bash
clawsqlite knowledge maintenance prune|gc --days N [--dry-run]
```

**Description:**

- Reads all article IDs and file paths from the DB;
- Scans `articles_dir` for:
  - `.bak_YYYYMMDD...` files older than N days;
  - markdown files whose ID/path do not match DB records (orphans).
- Scans DB for rows whose `local_file_path` does not exist on disk
  (broken records).
- In `--dry-run` mode: outputs a report of orphans / bak_to_delete /
  broken_records;
- Otherwise: deletes orphan + old backup files.

**Classification:**

- The core logic is a **plumbing wrapper candidate** and maps naturally to
  `clawsqlite fs list-orphans` + `clawsqlite fs gc`:
  - scanning `articles_dir` vs DB paths;
  - deciding which `.bak_` files to delete;
  - reporting orphans / broken records.
- The specific `.bak_deleted_` naming and retention policy may stay in the
  `knowledge` layer, but the generic FS+DB GC logic should move into
  `clawsqlite fs`.

---

## 2. Summary classification

In short:

- **Application-level (stay under `clawsqlite knowledge ...`):**
  - `ingest`
  - `search`
  - `show`
  - `export`
  - `update`
  - `delete`
  - `reindex --check`
  - `reindex --fix-missing`

- **Plumbing wrapper candidates (should be rebuilt using `db/index/fs`):**
  - `embed-from-summary` -> `embed column` with KB defaults
  - `reindex --rebuild [--fts] [--vec]` -> `index check` + `index rebuild`
  - `maintenance` (prune/gc) -> `fs list-orphans` + `fs gc` (+ `db vacuum` as needed)

Future work during the refactor can:

- keep `clawsqlite knowledge ...` as the namespace for these
  commands;
- keep expanding the `db/index/fs/embed` plumbing layer; and
- gradually rewrite wrapper candidates to call those primitives.
