# clawsqlite (knowledge)

**Languages:** English | [中文说明](README_zh.md)

`clawsqlite` is a CLI toolbox for SQLite‑based applications in
[OpenClaw](https://github.com/openclaw/openclaw). The first built‑in
application is a local Markdown + SQLite knowledge base.

This repo currently focuses on the **knowledge** app:

- commands are exposed under `clawsqlite knowledge ...` for users/skills.

A local Markdown + SQLite knowledge base for OpenClaw, designed for both
humans and agents.

The knowledge app helps you:

- Ingest URLs or raw text as Markdown files + SQLite records
- Run fast full‑text search over your notes and scraped articles
- Optionally enable vector search via an external embedding service
- Regenerate titles/summaries/tags via heuristics or a small LLM
- Keep the KB healthy with explicit maintenance commands (reindex/check/fix + maintenance prune/gc)

> **Status**: already used in real OpenClaw setups. The schema and CLI are kept small and stable on purpose.

---

## 1. Features

- **Pure SQLite backend**
  - `articles` table as source of truth
  - `articles_fts` FTS5 table for full‑text search
  - `articles_vec` vec0 table for vector search (optional)
- **Markdown storage**
  - Each article is stored as `articles/<id>__<slug>.md`
  - Markdown files include a small METADATA header + MARKDOWN body section
- **Configurable root**
  - All data lives under a single root directory
  - DB and articles dir default to `<root>/knowledge.sqlite3` and `<root>/articles` (see env overrides below)
- **Embeddings + LLM (optional)**
  - Embeddings: OpenAI‑compatible `/v1/embeddings` API
  - Small LLM: OpenAI‑compatible `/v1/chat/completions` API
- **Tag generation & search ranking**
  - Tags are generated from article content via heuristics or a small LLM
  - When `jieba` is installed, tags are ordered by importance using
    TextRank/TF‑IDF (and optionally a semantic centrality rerank when
    embeddings are enabled)
  - Search ranking uses tag/query matching as an additional signal on top
    of FTS and vector similarity
- **CLI first**
  - Simple subcommands: `ingest`, `search`, `show`, `export`, `update`, `delete`, `reindex`

---

## 2. Requirements

The knowledge app expects an environment similar to the OpenClaw container:

- Python 3.10+ with `sqlite3` and FTS5 enabled
- Python dependencies:
  - `jieba` (optional but strongly recommended for Chinese tag extraction)
  - `pypinyin` (optional; used to generate pinyin slugs for CJK titles)
- sqlite extensions (optional but recommended):
  - `libsimple.so` (tokenizer `simple`) for better CJK tokenization
  - `vec0.so` from [sqlite-vec](https://github.com/asg017/sqlite-vec)
- Network access to your embedding / small LLM HTTP endpoints (if you enable those features)

The repo assumes these paths by default (you can override them):

- Tokenizer extension: `/usr/local/lib/libsimple.so`
- vec0 extension: auto-discovered under `/app/node_modules/**/vec0.so` or system lib dirs

In a fresh environment you typically need to:

- Install `jieba` via pip:

  ```bash
  pip install jieba
  ```

- For `libsimple.so` and `vec0.so`:
  - In the OpenClaw container these are preinstalled.
  - On a custom system you can either:
    - Use distro packages if available (check your Linux distribution), or
    - Build from source following the upstream docs:
      - sqlite-vec: <https://github.com/asg017/sqlite-vec>
      - simple tokenizer: see the OpenClaw docs for building `libsimple.so`.
  - If these extensions are missing, the knowledge app will automatically degrade to:
    - SQLite built‑in tokenizer for FTS
    - If `jieba` is available, optionally pre-segment CJK text in Python for better
      Chinese recall (controlled by `CLAWSQLITE_FTS_JIEBA=auto|on|off`)
    - FTS‑only mode when vec0 is unavailable.

---

## 3. Installation

### 3.1 From PyPI (recommended for general use)

Once published, the simplest way to use `clawsqlite` is via PyPI:

```bash
pip install clawsqlite

# Then
clawsqlite knowledge --help
```

This installs the `clawsqlite` console script so you can call the CLI from
anywhere in your environment.

### 3.2 From source (development / OpenClaw workspace)

Clone the repo:

```bash
git clone git@github.com:ernestyu/clawsqlite.git
cd clawsqlite
```

(Inside OpenClaw’s workspace this repo may already be present at
`/home/node/.openclaw/workspace/clawsqlite`.)

You can run the knowledge app via the main shell entrypoint:

```bash
# From the repo root
./bin/clawsqlite knowledge --help

# Or explicitly choose a Python binary (e.g. your venv)
CLAWSQLITE_PYTHON=/opt/venv/bin/python ./bin/clawsqlite knowledge --help
```

The recommended CLI entrypoint for skills/users is:

```bash
clawsqlite knowledge ...
```

Use:

```bash
clawsqlite knowledge ...
```

---

## 4. Configuration

### 4.1 Root & paths

The knowledge app determines its root + DB + articles directory via CLI
flags + env + defaults.

Priority for root:

1. CLI: `--root`
2. Env: `CLAWSQLITE_ROOT`
3. Default: `<current working dir>/knowledge_data`

DB path:

- `--db` > `CLAWSQLITE_DB` > `<root>/knowledge.sqlite3`

Articles dir:

- `--articles-dir` > `CLAWSQLITE_ARTICLES_DIR` > `<root>/articles`

### 4.2 Project `.env`

A **project‑level `.env` file** is the primary configuration source. Start from the example:

```bash
cp ENV.example .env
# then edit .env
```

`ENV.example` contains fields like:

```env
# Embedding service (required for vector search)
EMBEDDING_BASE_URL=https://embed.example.com/v1
EMBEDDING_MODEL=your-embedding-model
EMBEDDING_API_KEY=sk-your-embedding-key
CLAWSQLITE_VEC_DIM=1024

# Small LLM (optional)
SMALL_LLM_BASE_URL=https://llm.example.com/v1
SMALL_LLM_MODEL=your-small-llm
SMALL_LLM_API_KEY=sk-your-small-llm-key

# Root override (optional)
# CLAWSQLITE_ROOT=/path/to/knowledge_root
# CLAWSQLITE_DB=/path/to/knowledge.sqlite3
# CLAWSQLITE_ARTICLES_DIR=/path/to/articles
```

At runtime, `clawsqlite knowledge ...` (and `python -m clawsqlite_cli`) will
auto‑load a project‑level `.env` from the current working directory.
Existing environment variables are **not** overridden. In OpenClaw containers
this is usually done via the agent’s env config instead of editing `.env`.

### 4.3 Embedding configuration

Embeddings are used for vector search (`articles_vec`) and can be disabled if you only want FTS.

Required env (typically via `.env`):

- `EMBEDDING_MODEL` – model name used by your embedding endpoint
- `EMBEDDING_BASE_URL` – base URL, e.g. `https://embed.example.com/v1`
- `EMBEDDING_API_KEY` – bearer token
- `CLAWSQLITE_VEC_DIM` – embedding dimension (e.g. `1024` for BAAI/bge-m3)

The knowledge app will:

- Use these env vars in `clawsqlite_knowledge.embed.get_embedding()` (via httpx POST to `/v1/embeddings`)
- Use `CLAWSQLITE_VEC_DIM` to define `embedding float[DIM]` in `articles_vec`

If any of these are missing, **vector features are treated as disabled**:

- `embedding_enabled()` returns `False`
- `ingest` will not call the embedding API
- `search` in `mode=hybrid` will auto‑downgrade to FTS‑only and print a `NEXT` hint

### 4.4 Tag generation & semantic rerank

By default the knowledge app tries to keep `title`, `summary`, and `tags`
reasonably populated using heuristics and (optionally) a small LLM.

Tag generation has a few modes controlled by `CLAWSQLITE_TAGS_SEMANTIC`:

- `auto` (default):
  - If both Embedding and `jieba` are available, use TextRank/TF‑IDF to
    pick candidates and then apply a **semantic centrality rerank** so
    tags closer to the article’s main theme float to the top.
  - If `jieba` is available but embeddings are not, use pure
    TextRank/TF‑IDF; tag order still reflects importance.
  - If `jieba` is not available, fall back to a lightweight keyword
    extractor and emit a `NEXT` hint suggesting you install `jieba`.
- `on`: force semantic centrality rerank when Embedding + `jieba` are both
  available.
- `off`: disable semantic rerank; always use the non‑semantic behavior for
  the current environment.

Search ranking also uses tags as a small but important signal:

- When `jieba` is available (tags are ordered by importance), we compute a
  continuous tag match score in [0,1] based on how many query keywords
  exactly match the top tags and how early they appear.
- When `jieba` is not available, we fall back to a simple 0/1 bonus for
  any exact tag match, to avoid over‑interpreting a noisy tag order.

### 4.4 Small LLM configuration (optional)

For better titles/summaries/tags you can configure a small LLM endpoint:

```env
SMALL_LLM_BASE_URL=https://llm.example.com/v1
SMALL_LLM_MODEL=your-small-llm
SMALL_LLM_API_KEY=sk-your-small-llm-key
```

Then use `--gen-provider llm` when ingesting or updating records. The
knowledge app will call an OpenAI‑compatible chat completions API to
generate `title`, `summary`, and `tags`.

If these env vars are not set, `provider=openclaw` uses heuristics only (no network calls).

### 4.5 Scraper configuration

The knowledge app does **not** implement web scraping itself. For `--url`
ingest it runs an external scraper command, configured via:

- CLI: `--scrape-cmd`
- Env: `CLAWSQLITE_SCRAPE_CMD`

Recommended usage:

```env
CLAWSQLITE_SCRAPE_CMD="node /path/to/scrape.js --some-flag"
```

The knowledge app will:

- Load this value from `.env` (stripping outer quotes)
- Use `shlex.split()` to build argv (no `shell=True` by default)
- Append the URL as the last argument if you don’t use `{url}`

Scraper output formats:

- **New format (recommended):**

  ```text
  --- METADATA ---
  Title: Some article title
  Author: Someone
  ...

  --- MARKDOWN ---
  # Markdown heading
  Body...
  ```

- **Old format (still supported):**

  ```text
  Title: Some article title
  # Markdown heading
  Body...
  ```

The knowledge app will parse these into `title` and markdown body.

---

## 5. Quickstart

### 5.1 Minimal setup

1. **Clone & cd**

   ```bash
   git clone git@github.com:ernestyu/clawsqlite.git
   cd clawsqlite
   ```

2. （可选）在你的外层环境中配置好根目录和 Embedding/LLM 相关 env，或
   直接在运行时通过 `--root/--db/--articles-dir` 传入。这里不再强依赖
   项目内置 `.env` 加载逻辑。

3. **First ingest (text)** – this also creates the DB and basic tables:

   ```bash
   clawsqlite knowledge ingest \
     --text "Hello clawsqlite" \
     --title "First note" \
     --category dev \
     --tags test \
     --gen-provider off \
     --json
   ```

   This will:

   - Create `<root>/knowledge.sqlite3`
   - Create `<root>/articles/000001__first-note.md`
   - Index the record in FTS (and vec if embedding is configured)

4. **Search it back**:

   ```bash
   clawsqlite knowledge search "Hello" --mode fts --json
   ```

   You should see the record you just created.

### 5.2 Ingest a URL

Assuming you have a scraper command set in `.env`:

```bash
clawsqlite knowledge ingest \
  --url "https://example.com/article" \
  --category web \
  --tags example \
  --gen-provider openclaw \
  --json
```

This will:

- Call your scraper
- Extract title + markdown body
- Optionally generate `summary`/`tags`
- Store everything in DB + markdown

### 5.3 Updating an existing URL (`--update-existing`)

If you know a URL’s content has changed and you want to refresh the existing record:

```bash
clawsqlite knowledge ingest \
  --url "https://example.com/article" \
  --gen-provider openclaw \
  --update-existing \
  --json
```

Semantics:

- If a record with this `source_url` exists (and is not deleted), and `--update-existing` is set:
  - The knowledge app updates that record’s `title` / `summary` / `tags` / `category` / `priority`
  - Keeps the same `id`
  - Rewrites the markdown file
  - Updates FTS and vec indexes
- If no such record exists, it behaves like a normal ingest.

Note: `source_url` has a UNIQUE index for non‑empty, non‑`Local` values, so each URL maps to at
most one active record.

---

## 6. CLI Overview

All commands share common flags (`--root`, `--db`, `--articles-dir`, `--json`, `--verbose`).
Run `clawsqlite knowledge <command> --help` for full details.

### 6.1 ingest

```bash
clawsqlite knowledge ingest --url URL [options]
clawsqlite knowledge ingest --text TEXT [options]
```

Key options:

- `--url` / `--text`
- `--title`, `--summary`, `--tags`, `--category`, `--priority`
- `--gen-provider {openclaw,llm,off}`
- `--scrape-cmd` (or env `CLAWSQLITE_SCRAPE_CMD`)
- `--update-existing` (for URL mode)

### 6.2 search

```bash
clawsqlite knowledge search "query" --mode hybrid --topk 20 --json
```

Modes:

- `hybrid` – combine vec + FTS
- `fts` – full‑text only
- `vec` – vector only (requires embedding enabled)

Other flags:

- `--candidates` – candidate pool before re‑ranking
- `--llm-keywords {auto,on,off}` – FTS query expansion
- `--gen-provider` – used only if `llm-keywords=auto` and FTS hits are too few
- Filters: `--category`, `--tag`, `--since`, `--priority`, `--include-deleted`

### 6.3 show / export / update / delete

- `show` – dump one record (optionally with full markdown content)
- `export` – write a record to a `.md` or `.json` file
- `update` – patch fields or regenerate via generator (id/source_url/created_at are treated as read-only)
- `delete` – soft delete by default (sets `deleted_at`); `--hard` for permanent removal

All of these commands now **check that the DB file exists** before opening it:

- If `--root/--db` or `.env` point to a non‑existent DB path, they will report:

  ```text
  ERROR: db not found at /path/to/db. Check --root/--db or .env configuration.
  ```

  instead of silently creating an empty DB and then failing with `id not found`.

### 6.4 reindex

Maintenance operations:

- `reindex --check` – report missing fields/indexes
- `reindex --fix-missing` – regen fields/indexes using current generator
- `reindex --rebuild --fts` – rebuild FTS index (via `clawsqlite index rebuild`)
- `reindex --rebuild --vec` – clear vec index **only** (no embedding); use
  `clawsqlite knowledge embed-from-summary` to refill embeddings.

The check output includes flags like `vec_available` and `embedding_enabled` to help you
understand whether vec features are actually usable for the current DB.

---

### 6.5 maintenance

```bash
clawsqlite knowledge maintenance prune --days 3 --dry-run
```

This scans for orphaned files, old `.bak_*` backups, and broken DB paths.
Use `--dry-run` to preview deletions; `maintenance gc` is an alias of `prune`.

---

## 7. Notes on File Naming & Titles

Markdown files are named:

```text
<id:06d>__<slugified-title>.md
```

- `id` comes from the `articles` table
- `slugified-title` is derived from the title:
  - If `pypinyin` is available, CJK tokens are converted to pinyin;
  - ASCII letters/digits are preserved; other symbols become `-`;
  - Repeated `-` are collapsed; empty results fall back to `untitled`.

For CJK titles, the filename is typically a pinyin‑based slug. If `pypinyin`
is not installed, it may fall back to `untitled`. This does not affect functionality:

- The real title is stored in the DB
- Search operates on DB fields and FTS, not filenames

We may refine this strategy in future (e.g. supporting CJK slugs or ID‑only filenames), but the
current format is stable and works well with existing tools.

---

## 8. 中文说明（简要）

`clawsqlite` 提供的知识库应用是一个基于 SQLite + FTS5 + sqlite-vec
的本地知识库 CLI，主要特性：

- 文章元数据存到 `articles` 表，全文索引用 FTS5，向量检索用 sqlite-vec
- 每篇文章同时会写成一个 markdown 文件，包含 `--- METADATA ---` 和 `--- MARKDOWN ---`
- 支持：
  - `ingest`：从 URL 或纯文本入库
  - `search`：FTS / 向量 / 混合模式
  - `show` / `export` / `update` / `delete` / `reindex` / `maintenance`

### 快速开始

1. 克隆仓库：

   ```bash
   git clone git@github.com:ernestyu/clawsqlite.git
   cd clawsqlite
   ```

2. 在运行环境中配置好 `CLAWSQLITE_ROOT` / `CLAWSQLITE_DB` 等路径以及
   EMBEDDING_* / SMALL_LLM_* 等变量，或直接在命令行通过
   `--root/--db/--articles-dir` 传入。这一步通常在 OpenClaw 的 agent
   配置中完成。

3. 第一次入库（文本）：

   ```bash
   clawsqlite knowledge ingest \
     --text "你好，clawsqlite" \
     --title "第一次笔记" \
     --category test \
     --tags demo \
     --gen-provider off
   ```

4. 搜索：

   ```bash
   clawsqlite knowledge search "clawsqlite" --mode fts
   ```

### URL 重抓 & 刷新

当你知道某篇文章更新了，并且之前已经用 URL 入过库，可以用：

```bash
clawsqlite knowledge ingest \
  --url "https://example.com/article" \
  --update-existing
```

行为：

- `source_url` 已存在时：更新同一条记录（title/summary/tags/category/priority），并重写 markdown + 索引
- `source_url` 不存在时：正常新增一条记录

`articles.source_url` 对非空、非 `Local` 的 URL 有唯一约束，保证一个 URL 对应最多一条记录。

---

如果你在使用过程中遇到问题或有改进建议，欢迎在仓库里开 issue / PR。

---

## License

MIT © Ernest Yu
