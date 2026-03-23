# -*- coding: utf-8 -*-
"""Alias entrypoint for the knowledge namespace.

This module exposes the knowledge CLI under:

  `clawsqlite knowledge ...`
"""
from __future__ import annotations

from typing import List, Optional

from .cli import build_parser as _build_kb_parser
from .utils import load_project_env


def build_parser():
    """Build the knowledge CLI parser."""

    p = _build_kb_parser()
    p.prog = "clawsqlite knowledge"
    p.description = "clawsqlite knowledge base CLI."
    return p


def main(argv: Optional[List[str]] = None) -> int:
    # Load project-level .env so knowledge config works when invoked via
    # the top-level `clawsqlite` entrypoint.
    load_project_env()
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    import sys as _sys

    raise SystemExit(main(_sys.argv[1:]))
