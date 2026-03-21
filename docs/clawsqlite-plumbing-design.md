# clawsqlite Plumbing Layer Design

This document describes the proposed **"plumbing" layer** for the
`clawsqlite` CLI – low-level, generic commands around SQLite, full-text
/ vector indexes, and the associated filesystem layout.

These commands are intended to be:

- **Generic** – usable by multiple applications (KB, reading, future apps);
- **Predictable** – do one thing, with clear input/output;
- **Composable** – higher-level "porcelain" commands (e.g. `clawsqlite kb`
  or `clawsqlite reading`) should be able to call them internally.

The CLI layout is:

```bash
clawsqlite db ...     # raw SQLite operations (schema/exec/backup/vacuum)
clawsqlite index ...  # generic FTS / vector index operations
clawsqlite fs ...     # filesystem + DB consistency helpers
```

Below, each command is described with:

- **What it does**
- **When to use it** (typical scenarios)
- **CLI signature**
- **Concrete examples**

---

## 1. `clawsqlite db` – raw SQLite operations

These commands work on a single SQLite database file and do **not** assume
any specific schema (no `articles`, no `category`, etc.). They are generic
maintenance / inspection tools.

### 1.1 `clawsqlite db schema`

**What it does**

Prints the schema (tables, indexes, views) of a SQLite database, optionally
filtered to a single table.

**When to use it**

- You want to see **what tables/columns exist** in a DB (for debugging or
  documentation).
- You are writing a new app on top of an existing DB and need to understand
  its layout.

**Signature**

```bash
clawsqlite db schema --db PATH [--table NAME]
```

- `--db PATH` – path to the `.db` file
- `--table NAME` – optional; if provided, only show schema for that table

**Examples**

```bash
# Show full schema
clawsqlite db schema --db ~/.clawsqlite/knowledge.db

# Show only the schema for table 'articles'
clawsqlite db schema --db ~/.clawsqlite/knowledge.db --table articles
```

---

### 1.2 `clawsqlite db exec`

**What it does**

Executes arbitrary SQL against a SQLite database. This is a **low-level
escape hatch** – powerful but potentially dangerous if misused.

**When to use it**

- One-off data migrations (e.g. add a column, backfill some values).
- Manual fixes during development (e.g. reset a flag, delete test rows).
- Scripting: call from shell scripts when you need to run SQL and don't
  want to invoke the sqlite3 CLI directly.

**Signature**

```bash
clawsqlite db exec --db PATH (--sql SQL | --file SQL_FILE)
```

- `--db PATH` – path to the `.db` file
- `--sql SQL` – inline SQL string
- `--file SQL_FILE` – path to a `.sql` file containing statements

**Examples**

```bash
# Mark all low-priority articles as archived
clawsqlite db exec --db ~/.clawsqlite/knowledge.db \
  --sql "UPDATE articles SET archived = 1 WHERE priority <= 0;"

# Run a migration script
clawsqlite db exec --db ~/.clawsqlite/knowledge.db --file migrations/001_add_flags.sql
```

> NOTE: This is plumbing. Application-level commands (e.g. `kb migrate`)
> should wrap specific migrations instead of asking users to type raw SQL.

---

### 1.3 `clawsqlite db vacuum`

**What it does**

Runs `VACUUM` on the database: compacts the file, reclaims free space,
rebuilds the B-tree structures.

**When to use it**

- After deleting many rows (KB cleanup, reading history cleanup, etc.).
- Periodic maintenance to keep the DB small and efficient.

**Signature**

```bash
clawsqlite db vacuum --db PATH
```

**Examples**

```bash
# Compact the knowledge DB after heavy cleanup
clawsqlite db vacuum --db ~/.clawsqlite/knowledge.db
```

---

### 1.4 `clawsqlite db analyze`

**What it does**

Runs `ANALYZE` on the database: updates SQLite's internal statistics so
query planner can choose better indexes.

**When to use it**

- After large bulk imports (e.g. ingesting many articles / books).
- After changing indexes.

**Signature**

```bash
clawsqlite db analyze --db PATH
```

**Examples**

```bash
# After a large ingest
clawsqlite db analyze --db ~/.clawsqlite/knowledge.db
```

---

### 1.5 `clawsqlite db backup`

**What it does**

Creates a copy of a SQLite database to a specified path. Optionally adds a
timestamp.

**When to use it**

- Before risky operations (schema changes, bulk deletes).
- For periodic backups (e.g. cron job).

**Signature**

```bash
clawsqlite db backup --db PATH --out PATH [--add-timestamp]
```

- `--db PATH` – source DB
- `--out PATH` – destination path (file or directory)
- `--add-timestamp` – if set and `--out` is a directory, append a timestamped
  filename

**Examples**

```bash
# Backup to explicit path
clawsqlite db backup --db ~/.clawsqlite/knowledge.db --out backups/knowledge.db

# Backup with timestamped filename
clawsqlite db backup --db ~/.clawsqlite/knowledge.db --out backups --add-timestamp
# e.g. creates backups/knowledge-2026-03-21T06-30-00.db
```

---

## 2. `clawsqlite index` – FTS / vector index operations

These commands assume you have a table with some columns that are indexed
with FTS (full-text search) and/or a vector index. They do **not** assume
KB-specific columns like `category` or `priority`.

### 2.1 `clawsqlite index check`

**What it does**

Checks index consistency for a given table:

- verifies that FTS rows match base table rows;
- optionally verifies that vector index rows match base table rows.

**When to use it**

- Suspect index corruption or mismatch (e.g. after manual SQL updates).
- As part of a periodic health check.

**Signature**

```bash
clawsqlite index check \
  --db PATH \
  --table NAME \
  [--fts-col NAME] \
  [--vec-col NAME]
```

- `--db PATH` – database file
- `--table NAME` – base table name (e.g. `articles`)
- `--fts-col NAME` – optional, FTS index column name
- `--vec-col NAME` – optional, vector index column name

**Examples**

```bash
# Check FTS index for articles.content_fts
clawsqlite index check \
  --db ~/.clawsqlite/knowledge.db \
  --table articles \
  --fts-col content_fts

# Check both FTS and vector index
clawsqlite index check \
  --db ~/.clawsqlite/knowledge.db \
  --table articles \
  --fts-col content_fts \
  --vec-col embedding
```

Output could be a short report:

```text
[OK] FTS index matches base table (1234 rows)
[OK] Vector index matches base table (1234 rows)
```

or detailed warnings if mismatches are found.

---

### 2.2 `clawsqlite index rebuild`

**What it does**

Rebuilds one or both indexes (FTS / vector) for a table based on the
current base data.

**When to use it**

- After significant manual changes to base table rows.
- When `index check` reports mismatch.
- After upgrading the indexing scheme.

**Signature**

```bash
clawsqlite index rebuild \
  --db PATH \
  --table NAME \
  [--fts-col NAME] \
  [--vec-col NAME]
```

**Examples**

```bash
# Rebuild FTS index
clawsqlite index rebuild \
  --db ~/.clawsqlite/knowledge.db \
  --table articles \
  --fts-col content_fts

# Rebuild both FTS and vector index
clawsqlite index rebuild \
  --db ~/.clawsqlite/knowledge.db \
  --table articles \
  --fts-col content_fts \
  --vec-col embedding
```

> Application-level commands like `kb reindex` would typically wrap this
> with fixed `--table` / `--fts-col` / `--vec-col` arguments.

---

### 2.3 `clawsqlite index search` (optional core)

**What it does**

Provides a **generic** search primitive on top of FTS and/or vector
indexes:

- given a query string, returns row IDs and scores; 
- supports FTS-only, vector-only, or hybrid scoring.

This command does **not** know about KB-specific fields (`title`,
`category`, etc.). It is intended as a low-level core that `kb search` or
`reading search` can call.

**Signature**

```bash
clawsqlite index search \
  --db PATH \
  --table NAME \
  [--fts-col NAME] \
  [--vec-col NAME] \
  --query STRING \
  [--limit N]
```

**Examples**

```bash
# Hybrid search on articles
clawsqlite index search \
  --db ~/.clawsqlite/knowledge.db \
  --table articles \
  --fts-col content_fts \
  --vec-col embedding \
  --query "LLM quantization" \
  --limit 20
```

Output (for plumbing) could be JSON lines:

```json
{"rowid": 123, "fts_score": 1.23, "vec_score": 0.87, "hybrid_score": 0.95}
{"rowid": 45,  "fts_score": 0.98, "vec_score": 0.90, "hybrid_score": 0.94}
...
```

Application-level search commands would then:

- read these row IDs;
- join with the base table to fetch titles, categories, etc.;
- format user-facing output.

---

## 3. `clawsqlite fs` – filesystem + DB helpers

Many SQLite-backed apps pair a DB with a set of files (e.g. Markdown
articles). These commands help keep the two in sync. They **do not**
encode KB-specific notions like `category`, only the fact that:

- there is a root directory of files; and
- the DB has some mapping to those files (e.g., a `path` column).

### 3.1 `clawsqlite fs list-orphans`

**What it does**

Lists mismatches between the DB and filesystem:

- files on disk with no matching DB row;
- DB rows pointing to missing files.

**When to use it**

- Before cleanup, to see what would be affected.
- During debugging when something "disappears" from the app but not from
  disk (or vice versa).

**Signature**

```bash
clawsqlite fs list-orphans \
  --root DIR \
  --db PATH \
  --table NAME \
  --path-col NAME
```

- `--root DIR` – root directory for content files
- `--db PATH` – database path
- `--table NAME` – table that stores file references
- `--path-col NAME` – column in that table that stores relative paths

**Examples**

```bash
# List orphans for KB articles
clawsqlite fs list-orphans \
  --root ~/kb/articles \
  --db ~/.clawsqlite/knowledge.db \
  --table articles \
  --path-col relpath
```

Output could be a simple report:

```text
[FS_ONLY] articles/old-note-1.md
[DB_ONLY] rowid=42 path="articles/missing-note.md"
```

---

### 3.2 `clawsqlite fs gc`

**What it does**

Performs a **garbage-collection** pass over the filesystem + DB:

- optionally deletes files that are not referenced in the DB;
- optionally removes DB rows whose files are missing;
- can be run in dry-run mode first.

**When to use it**

- Periodic cleanup of a KB / reading library to remove stale files.
- After manual file operations (moving/deleting files outside the tool).

**Signature**

```bash
clawsqlite fs gc \
  --root DIR \
  --db PATH \
  --table NAME \
  --path-col NAME \
  [--delete-fs-orphans] \
  [--delete-db-orphans] \
  [--dry-run]
```

**Examples**

```bash
# Dry-run: see what would be cleaned up
clawsqlite fs gc \
  --root ~/kb/articles \
  --db ~/.clawsqlite/knowledge.db \
  --table articles \
  --path-col relpath \
  --delete-fs-orphans \
  --delete-db-orphans \
  --dry-run

# Actual cleanup
clawsqlite fs gc \
  --root ~/kb/articles \
  --db ~/.clawsqlite/knowledge.db \
  --table articles \
  --path-col relpath \
  --delete-fs-orphans \
  --delete-db-orphans
```

Application-level commands like `kb maintenance` could wrap this with
predefined `--root` / `--table` / `--path-col` values.

---

### 3.3 `clawsqlite fs reconcile` (optional)

**What it does**

Attempts to reconcile mismatches between DB and filesystem:

- for DB rows pointing to missing files, optionally create empty stub
  files so editors can recreate content;
- for files without DB rows, optionally register them in a special import
  table or queue.

**When to use it**

- When you want to restore invariant "every DB row has a file" without
  deleting the DB rows.
- When you have manually dropped Markdown files into the content folder and
  want to import them.

**Signature**

```bash
clawsqlite fs reconcile \
  --root DIR \
  --db PATH \
  --table NAME \
  --path-col NAME \
  [--create-missing-files] \
  [--register-orphan-files]
```

**Examples**

```bash
# Create empty files for DB rows whose content files are missing
clawsqlite fs reconcile \
  --root ~/kb/articles \
  --db ~/.clawsqlite/knowledge.db \
  --table articles \
  --path-col relpath \
  --create-missing-files

# Register orphan files into an 'import_queue' table (hypothetical)
clawsqlite fs reconcile \
  --root ~/kb/articles \
  --db ~/.clawsqlite/knowledge.db \
  --table articles \
  --path-col relpath \
  --register-orphan-files
```

Concrete behavior (e.g. which table to use for import) would be fleshed out
once KB/reading use-cases are clearer, but the CLI surface stays generic.

---

## 4. How applications would use this

- **KB (`clawsqlite kb ...`)**:
  - `kb reindex` → wraps `index check` + `index rebuild` with fixed table/cols;
  - `kb maintenance` → wraps `fs gc` + `db vacuum` + `index check`;
  - `kb search` → internally calls `index search` then joins `rowid` to
    `articles` table.

- **Reading (`clawsqlite reading ...`)**:
  - `reading ingest-epub` → writes rows to a `reading_items` table, then
    calls `index rebuild` for that table;
  - `reading maintenance` → wraps `fs gc` for the reading root.

This way, **all the KB/reading-specific verbs** stay under their own
namespaces (`kb`, `reading`), while the low-level DB/FS/index machinery is
consolidated and reusable.
