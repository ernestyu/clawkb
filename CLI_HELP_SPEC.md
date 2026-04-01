# CLI Help Spec (generated from argparse)

## clawsqlite knowledge --help
usage: clawsqlite knowledge [-h] [--root ROOT] [--db DB]
                            [--articles-dir ARTICLES_DIR]
                            [--tokenizer-ext TOKENIZER_EXT]
                            [--vec-ext VEC_EXT] [--json] [--verbose]
                            {build-interest-clusters,ingest,search,show,export,update,delete,reindex,inspect-interest-clusters,embed-from-summary,maintenance}
                            ...

OpenClaw knowledge base CLI (SQLite + FTS5 + sqlite-vec).

positional arguments:
  {build-interest-clusters,ingest,search,show,export,update,delete,reindex,inspect-interest-clusters,embed-from-summary,maintenance}
    build-interest-clusters
                        Build interest clusters from existing article
                        embeddings
    ingest              Ingest a URL or a text into the KB
    search              Search the KB (fts/vec/hybrid)
    show                Show one record
    export              Export one record to file
    update              Update one record (patch or regen)
    delete              Delete one record (soft by default)
    reindex             Maintenance: check/fix/rebuild
    inspect-interest-clusters
                        Inspect interest cluster radius + PCA scatter plot
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

## clawsqlite knowledge build-interest-clusters --help
usage: clawsqlite knowledge build-interest-clusters [-h] [--root ROOT]
                                                    [--db DB]
                                                    [--articles-dir ARTICLES_DIR]
                                                    [--tokenizer-ext TOKENIZER_EXT]
                                                    [--vec-ext VEC_EXT]
                                                    [--json] [--verbose]
                                                    [--min-size MIN_SIZE]
                                                    [--max-clusters MAX_CLUSTERS]

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
  --min-size MIN_SIZE   Minimum cluster size (articles per cluster)
  --max-clusters MAX_CLUSTERS
                        Maximum number of clusters to keep

## clawsqlite knowledge inspect-interest-clusters --help
usage: clawsqlite knowledge inspect-interest-clusters [-h] [--root ROOT]
                                                      [--db DB]
                                                      [--articles-dir ARTICLES_DIR]
                                                      [--tokenizer-ext TOKENIZER_EXT]
                                                      [--vec-ext VEC_EXT]
                                                      [--json] [--verbose]
                                                      [--vec-dim VEC_DIM]
                                                      [--no-plot]

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
  --vec-dim VEC_DIM     Embedding dimension (optional, default:
                        CLAWSQLITE_VEC_DIM / auto)
  --no-plot             Only print stats, do not generate PNG plot

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

... (other subcommands unchanged)

## clawsqlite knowledge report-interest --help
usage: clawsqlite knowledge report-interest [-h] [--root ROOT] [--db DB]
                                            [--articles-dir ARTICLES_DIR]
                                            [--tokenizer-ext TOKENIZER_EXT]
                                            [--vec-ext VEC_EXT] [--json]
                                            [--verbose] [--days DAYS]
                                            [--from DATE_FROM] [--to DATE_TO]
                                            [--vec-dim VEC_DIM]
                                            [--out-dir OUT_DIR] [--lang LANG]
                                            [--format {md,html}] [--no-pdf]

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
  --days DAYS           Lookback window in days (ignored if --from/--to
                        provided)
  --from DATE_FROM      Start date (YYYY-MM-DD)
  --to DATE_TO          End date (YYYY-MM-DD, exclusive)
  --vec-dim VEC_DIM     Embedding dimension (optional, default:
                        CLAWSQLITE_VEC_DIM / auto)
  --out-dir OUT_DIR     Root directory for reports (default: ./reports)
  --lang LANG           Report language (en/zh). Default:
                        $CLAWSQLITE_REPORT_LANG or en
  --format {md,html}    Additional output format: 'md' (default) or 'html'
                        (also write report.html via pandoc)
  --no-pdf              Do not run pandoc to generate PDF
