---
name: clawsqlite-knowledge
description: OpenClaw-facing skill for the clawsqlite knowledge base. Provides URL ingest, full-text / vector search, and basic maintenance via the ./bin/clawsqlite knowledge entrypoint.
---

# Skill: clawsqlite knowledge (local Markdown + SQLite knowledge base)

This skill describes how an OpenClaw agent should interact with a clawsqlite knowledge
instance that lives on the same machine.

> **Assumptions:**
> - The clawsqlite knowledge repo has been cloned (e.g. under `/home/node/.openclaw/workspace/clawsqlite`).
> - A project-level `.env` exists in the repo root with embedding / vec /
>   scraper configuration.
> - The agent can run shell commands on the host.

## 1. Critical paths

- **Project root**: `<PATH_TO_CLAWSQLITE_REPO>`
- **Data root (default)**: `<PATH_TO_CLAWSQLITE_REPO>/knowledge_data`
- **DB path (default)**: `<PATH_TO_CLAWSQLITE_REPO>/knowledge_data/knowledge.sqlite3`
- **Articles dir (default)**: `<PATH_TO_CLAWSQLITE_REPO>/knowledge_data/articles/`

Most of these defaults can be overridden via `.env` (`CLAWSQLITE_ROOT`,
`CLAWSQLITE_DB`, `CLAWSQLITE_ARTICLES_DIR`), but an agent should treat them as
implementation details and always go through `./bin/clawsqlite knowledge`.

## 2. Environment requirements

The only environment variable an agent should set inline is the Python
interpreter to use for clawsqlite knowledge (if the system default is not correct):

```bash
export CLAWSQLITE_PYTHON=/opt/venv/bin/python
```

All other configuration (embedding endpoints, vec extension path, scraper
command, root override) should live in the project `.env` and be managed by
humans / ops, not by the agent.

## 3. Main entrypoint

All operations MUST go through the shell entrypoint:

```bash
cd <PATH_TO_CLAWSQLITE_REPO>
./bin/clawsqlite knowledge <subcommand> [args...]
```

Examples below assume the repo lives at:

```text
/home/node/.openclaw/workspace/clawsqlite
```

## 4. Protocols

### 4.1 Ingest a web page or article

Ingest by URL (scraper and embedding config are taken from `.env`):

```bash
cd /home/node/.openclaw/workspace/clawsqlite
CLAWSQLITE_PYTHON=/opt/venv/bin/python \
  ./bin/clawsqlite knowledge ingest \
    --url "https://example.com/article" \
    --category "web" \
    --json
```

Notes:

- If the URL already exists and the agent wants to refresh the content, it
  should add `--update-existing`.
- `--category` can be used to tag different sources (e.g. `"微信公众号"`, `"github"`).

### 4.2 Hybrid search (FTS + vectors)

Search for relevant articles using the default hybrid mode:

```bash
cd /home/node/.openclaw/workspace/clawsqlite
CLAWSQLITE_PYTHON=/opt/venv/bin/python \
  ./bin/clawsqlite knowledge search "<QUERY_TEXT>" --json
```

The agent should parse the JSON output to retrieve:

- `id` – article id (for use with `show` / `export` / `update` / `delete`)
- `score` – relevance score
- `title`, `summary`, `category`, `tags`

If vector search is disabled (no embedding config), clawsqlite knowledge will
automatically fall back to FTS-only search.

### 4.3 Show a record

To inspect a single record:

```bash
cd /home/node/.openclaw/workspace/clawsqlite
CLAWSQLITE_PYTHON=/opt/venv/bin/python \
  ./bin/clawsqlite knowledge show --id <ID> --full
```

- `--full` includes the Markdown content in the output.
- Without `--full`, only metadata is printed.

### 4.4 Update fields or regenerate derived data

Patch title/summary/tags:

```bash
cd /home/node/.openclaw/workspace/clawsqlite
CLAWSQLITE_PYTHON=/opt/venv/bin/python \
  ./bin/clawsqlite knowledge update \
    --id <ID> \
    --title "New Title" \
    --summary "New long summary" \
    --tags "tag1,tag2" \
    --json
```

Regenerate summary/tags using the configured provider:

```bash
cd /home/node/.openclaw/workspace/clawsqlite
CLAWSQLITE_PYTHON=/opt/venv/bin/python \
  ./bin/clawsqlite knowledge update \
    --id <ID> \
    --regen summary \
    --gen-provider openclaw \
    --json
```

Regenerate embedding only:

```bash
cd /home/node/.openclaw/workspace/clawsqlite
CLAWSQLITE_PYTHON=/opt/venv/bin/python \
  ./bin/clawsqlite knowledge update \
    --id <ID> \
    --regen embedding \
    --json
```

### 4.5 Delete a record

Soft delete (mark as deleted, keep data for maintenance):

```bash
cd /home/node/.openclaw/workspace/clawsqlite
CLAWSQLITE_PYTHON=/opt/venv/bin/python \
  ./bin/clawsqlite knowledge delete --id <ID>
```

Agents should prefer soft delete; physical cleanup can be done by humans
or scheduled maintenance commands.

### 4.6 Maintenance and status

Basic index maintenance:

```bash
cd /home/node/.openclaw/workspace/clawsqlite
CLAWSQLITE_PYTHON=/opt/venv/bin/python \
  ./bin/clawsqlite knowledge reindex --check --fix
```

> Note: A dedicated `status` subcommand may be added in future versions of
> clawsqlite knowledge to summarise DB health and coverage. For now, agents can infer
> health from the success/failure of `reindex --check` and basic `search`
> calls.

## 5. Sovereignty rules (for agents)

1. **Single entrypoint**: Do not call `python -m clawsqlite knowledge` directly; always use
   `./bin/clawsqlite knowledge` from the repo root.
2. **Zero ad-hoc exports**: Only set `CLAWSQLITE_PYTHON` when needed. All other
   environment configuration must come from `.env`.
3. **No direct DB writes**: Do not manipulate the SQLite files directly;
   always go through the CLI.

With this protocol, a new agent can obtain full operational control over a
clawsqlite knowledge instance by learning a small, stable set of shell commands, without
needing to know the internal schema or Python package layout.
