# CLI Help Spec (generated from argparse)

## clawsqlite knowledge --help
usage: clawsqlite knowledge [-h] [--root ROOT] [--db DB]
                            [--articles-dir ARTICLES_DIR]
                            [--tokenizer-ext TOKENIZER_EXT]
                            [--vec-ext VEC_EXT] [--json] [--verbose]
                            {ingest,search,show,export,update,delete,reindex,embed-from-summary,maintenance} ...

clawsqlite knowledge base CLI.

positional arguments:
  {ingest,search,show,export,update,delete,reindex,embed-from-summary,maintenance}
    ingest              Ingest a URL or a text into the KB
    search              Search the KB (fts/vec/hybrid)
    show                Show one record
    export              Export one record to file
    update              Update one record (patch or regen)
    delete              Delete one record (soft by default)
    reindex             Maintenance: check/fix/rebuild
    embed-from-summary  Embed article summaries into articles_vec via plumbing
    maintenance         Maintenance: prune orphan/backup files and check paths

options:
  -h, --help            show this help message and exit
  --root ROOT           Root dir. Priority: CLI --root > $CLAWSQLITE_ROOT >
                        $CLAWSQLITE_ROOT_DEFAULT > <cwd>/knowledge_data.
  --db DB               SQLite db path. Priority: CLI --db > $CLAWSQLITE_DB >
                        <root>/knowledge.sqlite3
  --articles-dir ARTICLES_DIR
                        Articles markdown dir. Priority: CLI --articles-dir >
                        $CLAWSQLITE_ARTICLES_DIR > <root>/articles
  --tokenizer-ext TOKENIZER_EXT
                        Tokenizer extension path. Default:
                        /usr/local/lib/libsimple.so or
                        $CLAWSQLITE_TOKENIZER_EXT
  --vec-ext VEC_EXT     vec0 extension path. Default: auto-discover or
                        $CLAWSQLITE_VEC_EXT
  --json                Output JSON
  --verbose             Verbose logging

## clawsqlite knowledge delete --help
usage: clawsqlite knowledge delete [-h] [--root ROOT] [--db DB]
                                   [--articles-dir ARTICLES_DIR]
                                   [--tokenizer-ext TOKENIZER_EXT]
                                   [--vec-ext VEC_EXT] [--json] [--verbose]
                                   --id ID [--hard] [--remove-file]

options:
  -h, --help            show this help message and exit
  --root ROOT           Root dir. Priority: CLI --root > $CLAWSQLITE_ROOT >
                        $CLAWSQLITE_ROOT_DEFAULT > <cwd>/knowledge_data.
  --db DB               SQLite db path. Priority: CLI --db > $CLAWSQLITE_DB >
                        <root>/knowledge.sqlite3
  --articles-dir ARTICLES_DIR
                        Articles markdown dir. Priority: CLI --articles-dir >
                        $CLAWSQLITE_ARTICLES_DIR > <root>/articles
  --tokenizer-ext TOKENIZER_EXT
                        Tokenizer extension path. Default:
                        /usr/local/lib/libsimple.so or
                        $CLAWSQLITE_TOKENIZER_EXT
  --vec-ext VEC_EXT     vec0 extension path. Default: auto-discover or
                        $CLAWSQLITE_VEC_EXT
  --json                Output JSON
  --verbose             Verbose logging
  --id ID               Article id
  --hard                Hard delete (remove db row)
  --remove-file         When hard delete, permanently remove markdown file (no
                        backup)

## clawsqlite knowledge embed-from-summary --help
usage: clawsqlite knowledge embed-from-summary [-h] [--root ROOT] [--db DB]
                                               [--articles-dir ARTICLES_DIR]
                                               [--tokenizer-ext TOKENIZER_EXT]
                                               [--vec-ext VEC_EXT] [--json]
                                               [--verbose] [--where WHERE]
                                               [--limit LIMIT]
                                               [--offset OFFSET]

options:
  -h, --help            show this help message and exit
  --root ROOT           Root dir. Priority: CLI --root > $CLAWSQLITE_ROOT >
                        $CLAWSQLITE_ROOT_DEFAULT > <cwd>/knowledge_data.
  --db DB               SQLite db path. Priority: CLI --db > $CLAWSQLITE_DB >
                        <root>/knowledge.sqlite3
  --articles-dir ARTICLES_DIR
                        Articles markdown dir. Priority: CLI --articles-dir >
                        $CLAWSQLITE_ARTICLES_DIR > <root>/articles
  --tokenizer-ext TOKENIZER_EXT
                        Tokenizer extension path. Default:
                        /usr/local/lib/libsimple.so or
                        $CLAWSQLITE_TOKENIZER_EXT
  --vec-ext VEC_EXT     vec0 extension path. Default: auto-discover or
                        $CLAWSQLITE_VEC_EXT
  --json                Output JSON
  --verbose             Verbose logging
  --where WHERE         Optional SQL WHERE clause on articles (default:
                        undeleted with non-empty summary)
  --limit LIMIT         Optional LIMIT for batching
  --offset OFFSET       Optional OFFSET for batching

## clawsqlite knowledge export --help
usage: clawsqlite knowledge export [-h] [--root ROOT] [--db DB]
                                   [--articles-dir ARTICLES_DIR]
                                   [--tokenizer-ext TOKENIZER_EXT]
                                   [--vec-ext VEC_EXT] [--json] [--verbose]
                                   --id ID [--format {md,json}] --out OUT
                                   [--full]

options:
  -h, --help            show this help message and exit
  --root ROOT           Root dir. Priority: CLI --root > $CLAWSQLITE_ROOT >
                        $CLAWSQLITE_ROOT_DEFAULT > <cwd>/knowledge_data.
  --db DB               SQLite db path. Priority: CLI --db > $CLAWSQLITE_DB >
                        <root>/knowledge.sqlite3
  --articles-dir ARTICLES_DIR
                        Articles markdown dir. Priority: CLI --articles-dir >
                        $CLAWSQLITE_ARTICLES_DIR > <root>/articles
  --tokenizer-ext TOKENIZER_EXT
                        Tokenizer extension path. Default:
                        /usr/local/lib/libsimple.so or
                        $CLAWSQLITE_TOKENIZER_EXT
  --vec-ext VEC_EXT     vec0 extension path. Default: auto-discover or
                        $CLAWSQLITE_VEC_EXT
  --json                Output JSON
  --verbose             Verbose logging
  --id ID               Article id
  --format {md,json}    Export format
  --out OUT             Output file path
  --full                Export full markdown content

## clawsqlite knowledge ingest --help
usage: clawsqlite knowledge ingest [-h] [--root ROOT] [--db DB]
                                   [--articles-dir ARTICLES_DIR]
                                   [--tokenizer-ext TOKENIZER_EXT]
                                   [--vec-ext VEC_EXT] [--json] [--verbose]
                                   (--url URL | --text TEXT) [--title TITLE]
                                   [--summary SUMMARY] [--tags TAGS]
                                   [--category CATEGORY] [--priority PRIORITY]
                                   [--gen-provider {openclaw,llm,off}]
                                   [--max-summary-chars MAX_SUMMARY_CHARS]
                                   [--scrape-cmd SCRAPE_CMD]
                                   [--update-existing]

options:
  -h, --help            show this help message and exit
  --root ROOT           Root dir. Priority: CLI --root > $CLAWSQLITE_ROOT >
                        $CLAWSQLITE_ROOT_DEFAULT > <cwd>/knowledge_data.
  --db DB               SQLite db path. Priority: CLI --db > $CLAWSQLITE_DB >
                        <root>/knowledge.sqlite3
  --articles-dir ARTICLES_DIR
                        Articles markdown dir. Priority: CLI --articles-dir >
                        $CLAWSQLITE_ARTICLES_DIR > <root>/articles
  --tokenizer-ext TOKENIZER_EXT
                        Tokenizer extension path. Default:
                        /usr/local/lib/libsimple.so or
                        $CLAWSQLITE_TOKENIZER_EXT
  --vec-ext VEC_EXT     vec0 extension path. Default: auto-discover or
                        $CLAWSQLITE_VEC_EXT
  --json                Output JSON
  --verbose             Verbose logging
  --url URL             URL to ingest
  --text TEXT           Raw text content to ingest
  --title TITLE         Title override
  --summary SUMMARY     Summary override (long summary)
  --tags TAGS           Tags override (comma-separated)
  --category CATEGORY   Category, e.g. web/github/story
  --priority PRIORITY   Priority (0 default)
  --gen-provider {openclaw,llm,off}
                        Generator provider (llm affects tags only)
  --max-summary-chars MAX_SUMMARY_CHARS
                        Hard limit for summary length (chars)
  --scrape-cmd SCRAPE_CMD
                        Scraper command for URL ingest. Or env
                        CLAWSQLITE_SCRAPE_CMD
  --update-existing     If URL exists, refresh that record instead of
                        inserting a new one

## clawsqlite knowledge maintenance --help
usage: clawsqlite knowledge maintenance [-h] [--root ROOT] [--db DB]
                                        [--articles-dir ARTICLES_DIR]
                                        [--tokenizer-ext TOKENIZER_EXT]
                                        [--vec-ext VEC_EXT] [--json]
                                        [--verbose] [--days DAYS] [--dry-run]
                                        {prune,gc}

positional arguments:
  {prune,gc}            Maintenance action (prune=gc)

options:
  -h, --help            show this help message and exit
  --root ROOT           Root dir. Priority: CLI --root > $CLAWSQLITE_ROOT >
                        $CLAWSQLITE_ROOT_DEFAULT > <cwd>/knowledge_data.
  --db DB               SQLite db path. Priority: CLI --db > $CLAWSQLITE_DB >
                        <root>/knowledge.sqlite3
  --articles-dir ARTICLES_DIR
                        Articles markdown dir. Priority: CLI --articles-dir >
                        $CLAWSQLITE_ARTICLES_DIR > <root>/articles
  --tokenizer-ext TOKENIZER_EXT
                        Tokenizer extension path. Default:
                        /usr/local/lib/libsimple.so or
                        $CLAWSQLITE_TOKENIZER_EXT
  --vec-ext VEC_EXT     vec0 extension path. Default: auto-discover or
                        $CLAWSQLITE_VEC_EXT
  --json                Output JSON
  --verbose             Verbose logging
  --days DAYS           Backup retention in days (for .bak_ files)
  --dry-run             Dry run: only report, do not delete

## clawsqlite knowledge reindex --help
usage: clawsqlite knowledge reindex [-h] [--root ROOT] [--db DB]
                                    [--articles-dir ARTICLES_DIR]
                                    [--tokenizer-ext TOKENIZER_EXT]
                                    [--vec-ext VEC_EXT] [--json] [--verbose]
                                    [--check] [--fix-missing] [--rebuild]
                                    [--fts] [--vec]
                                    [--gen-provider {openclaw,llm,off}]

options:
  -h, --help            show this help message and exit
  --root ROOT           Root dir. Priority: CLI --root > $CLAWSQLITE_ROOT >
                        $CLAWSQLITE_ROOT_DEFAULT > <cwd>/knowledge_data.
  --db DB               SQLite db path. Priority: CLI --db > $CLAWSQLITE_DB >
                        <root>/knowledge.sqlite3
  --articles-dir ARTICLES_DIR
                        Articles markdown dir. Priority: CLI --articles-dir >
                        $CLAWSQLITE_ARTICLES_DIR > <root>/articles
  --tokenizer-ext TOKENIZER_EXT
                        Tokenizer extension path. Default:
                        /usr/local/lib/libsimple.so or
                        $CLAWSQLITE_TOKENIZER_EXT
  --vec-ext VEC_EXT     vec0 extension path. Default: auto-discover or
                        $CLAWSQLITE_VEC_EXT
  --json                Output JSON
  --verbose             Verbose logging
  --check               Check missing fields and index status
  --fix-missing         Fill missing fields and index rows
  --rebuild             Rebuild indexes
  --fts                 With --rebuild: rebuild FTS index
  --vec                 With --rebuild: clear vec index (no embedding)
  --gen-provider {openclaw,llm,off}
                        Generator provider for fix-missing (llm affects tags only)

## clawsqlite knowledge search --help
usage: clawsqlite knowledge search [-h] [--root ROOT] [--db DB]
                                   [--articles-dir ARTICLES_DIR]
                                   [--tokenizer-ext TOKENIZER_EXT]
                                   [--vec-ext VEC_EXT] [--json] [--verbose]
                                   [--mode {hybrid,fts,vec}] [--topk TOPK]
                                   [--candidates CANDIDATES]
                                   [--llm-keywords {auto,on,off}]
                                   [--gen-provider {openclaw,llm,off}]
                                   [--category CATEGORY] [--tag TAG]
                                   [--since SINCE] [--priority PRIORITY]
                                   [--include-deleted]
                                   query

positional arguments:
  query                 Query text

options:
  -h, --help            show this help message and exit
  --root ROOT           Root dir. Priority: CLI --root > $CLAWSQLITE_ROOT >
                        $CLAWSQLITE_ROOT_DEFAULT > <cwd>/knowledge_data.
  --db DB               SQLite db path. Priority: CLI --db > $CLAWSQLITE_DB >
                        <root>/knowledge.sqlite3
  --articles-dir ARTICLES_DIR
                        Articles markdown dir. Priority: CLI --articles-dir >
                        $CLAWSQLITE_ARTICLES_DIR > <root>/articles
  --tokenizer-ext TOKENIZER_EXT
                        Tokenizer extension path. Default:
                        /usr/local/lib/libsimple.so or
                        $CLAWSQLITE_TOKENIZER_EXT
  --vec-ext VEC_EXT     vec0 extension path. Default: auto-discover or
                        $CLAWSQLITE_VEC_EXT
  --json                Output JSON
  --verbose             Verbose logging
  --mode {hybrid,fts,vec}
                        Search mode
  --topk TOPK           Number of results to return
  --candidates CANDIDATES
                        Candidate pool size before final ranking
  --llm-keywords {auto,on,off}
                        Keyword expansion policy for FTS
  --gen-provider {openclaw,llm,off}
                        Keyword generator provider (used when llm-
                        keywords=auto/on)
  --category CATEGORY   Filter by category
  --tag TAG             Filter by tag substring
  --since SINCE         Filter created_at >= since (ISO, e.g.
                        2026-03-01T00:00:00Z)
  --priority PRIORITY   Priority filter, e.g. eq:0, gt:0, ge:1
  --include-deleted     Include deleted items

## clawsqlite knowledge show --help
usage: clawsqlite knowledge show [-h] [--root ROOT] [--db DB]
                                 [--articles-dir ARTICLES_DIR]
                                 [--tokenizer-ext TOKENIZER_EXT]
                                 [--vec-ext VEC_EXT] [--json] [--verbose]
                                 --id ID [--full]

options:
  -h, --help            show this help message and exit
  --root ROOT           Root dir. Priority: CLI --root > $CLAWSQLITE_ROOT >
                        $CLAWSQLITE_ROOT_DEFAULT > <cwd>/knowledge_data.
  --db DB               SQLite db path. Priority: CLI --db > $CLAWSQLITE_DB >
                        <root>/knowledge.sqlite3
  --articles-dir ARTICLES_DIR
                        Articles markdown dir. Priority: CLI --articles-dir >
                        $CLAWSQLITE_ARTICLES_DIR > <root>/articles
  --tokenizer-ext TOKENIZER_EXT
                        Tokenizer extension path. Default:
                        /usr/local/lib/libsimple.so or
                        $CLAWSQLITE_TOKENIZER_EXT
  --vec-ext VEC_EXT     vec0 extension path. Default: auto-discover or
                        $CLAWSQLITE_VEC_EXT
  --json                Output JSON
  --verbose             Verbose logging
  --id ID               Article id
  --full                Include markdown content

## clawsqlite knowledge update --help
usage: clawsqlite knowledge update [-h] [--root ROOT] [--db DB]
                                   [--articles-dir ARTICLES_DIR]
                                   [--tokenizer-ext TOKENIZER_EXT]
                                   [--vec-ext VEC_EXT] [--json] [--verbose]
                                   --id ID [--title TITLE] [--summary SUMMARY]
                                   [--tags TAGS] [--category CATEGORY]
                                   [--priority PRIORITY]
                                   [--regen {title,summary,tags,embedding,all}]
                                   [--gen-provider {openclaw,llm,off}]
                                   [--max-summary-chars MAX_SUMMARY_CHARS]

options:
  -h, --help            show this help message and exit
  --root ROOT           Root dir. Priority: CLI --root > $CLAWSQLITE_ROOT >
                        $CLAWSQLITE_ROOT_DEFAULT > <cwd>/knowledge_data.
  --db DB               SQLite db path. Priority: CLI --db > $CLAWSQLITE_DB >
                        <root>/knowledge.sqlite3
  --articles-dir ARTICLES_DIR
                        Articles markdown dir. Priority: CLI --articles-dir >
                        $CLAWSQLITE_ARTICLES_DIR > <root>/articles
  --tokenizer-ext TOKENIZER_EXT
                        Tokenizer extension path. Default:
                        /usr/local/lib/libsimple.so or
                        $CLAWSQLITE_TOKENIZER_EXT
  --vec-ext VEC_EXT     vec0 extension path. Default: auto-discover or
                        $CLAWSQLITE_VEC_EXT
  --json                Output JSON
  --verbose             Verbose logging
  --id ID               Article id
  --title TITLE         Patch: new title
  --summary SUMMARY     Patch: new summary
  --tags TAGS           Patch: new tags (comma-separated)
  --category CATEGORY   Patch: new category
  --priority PRIORITY   Patch: new priority
  --regen {title,summary,tags,embedding,all}
                        Regenerate fields (embedding=refresh vec from summary)
  --gen-provider {openclaw,llm,off}
                        Generator provider for regen (llm affects tags only)
  --max-summary-chars MAX_SUMMARY_CHARS
                        Hard limit for summary length (chars)
