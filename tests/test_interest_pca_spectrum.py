# -*- coding: utf-8 -*-
from __future__ import annotations

"""Inspect PCA spectrum of interest vectors.

This is an analysis helper (not a formal unit test). It rebuilds the
same interest vectors as `build_interest_clusters` and then computes a
PCA spectrum over those vectors to understand how variance is
distributed across dimensions.

Usage (from clawsqlite repo root):

    CLAWSQLITE_VEC_EXT=/app/node_modules/sqlite-vec-linux-arm64/vec0.so \
    MPLCONFIGDIR=/tmp/mplconfig \
    python -m tests.test_interest_pca_spectrum \
      --db /path/to/clawkb.sqlite3 \
      --vec-dim 1024

Outputs:

- Total number of interest vectors used.
- Top-N (default 64) principal components' variance ratios.
- Cumulative variance at a few candidate cutoffs (e.g. 32/64/128/256).

This is intentionally kept as a small, self-contained analysis script
rather than wired into the public CLI.
"""

import argparse
import os
import sqlite3
from pathlib import Path
from typing import List

import numpy as np

from clawsqlite_knowledge.interest import load_interest_vectors_from_db
from clawsqlite_knowledge.embed import _resolve_vec_dim
from clawsqlite_knowledge.db import _find_vec0_so


def _load_interest_vectors(conn: sqlite3.Connection, dim: int) -> np.ndarray:
    """Rebuild interest vectors in the same way as build_interest_clusters.

    This mirrors the SQL and mixing logic from
    `clawsqlite_knowledge.interest.build_interest_clusters` but returns a
    single 2D numpy array of shape (n_articles, dim).
    """
    _, vectors_1024, _ = load_interest_vectors_from_db(conn, dim=dim)
    vectors: List[np.ndarray] = [np.asarray(vec, dtype="float32") for vec in vectors_1024]

    if not vectors:
        raise SystemExit("No interest vectors could be constructed from DB")

    X = np.stack(vectors, axis=0)
    return X


def main() -> None:
    ap = argparse.ArgumentParser(description="Inspect PCA spectrum of interest vectors (internal)")
    ap.add_argument("--db", required=True, help="Path to clawkb.sqlite3")
    ap.add_argument("--vec-dim", type=int, default=None, help="Embedding dimension (optional)")
    ap.add_argument("--top", type=int, default=64, help="Number of leading PCs to print")
    args = ap.parse_args()

    db_path = Path(args.db)
    if not db_path.is_file():
        raise SystemExit(f"DB not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    # Best-effort load vec0 extension, mirroring other helpers.
    try:
        conn.enable_load_extension(True)
        ext = os.environ.get("CLAWSQLITE_VEC_EXT") or _find_vec0_so()
        if ext and ext.lower() != "none":
            conn.load_extension(ext)
    except Exception:
        pass

    # Row factory as tuples.
    conn.row_factory = None

    try:
        dim = args.vec_dim or _resolve_vec_dim()
        X = _load_interest_vectors(conn, dim=dim)
        n_samples, n_features = X.shape
        print(f"Loaded {n_samples} interest vectors of dimension {n_features} from {db_path}")

        # Center the data.
        X_centered = X - X.mean(axis=0, keepdims=True)

        # Compute SVD; for covariance matrix C = (1/n) X^T X, eigenvalues are (S^2 / n).
        # We only need the singular values S here.
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
        eigvals = (S ** 2) / float(n_samples)
        total_var = float(eigvals.sum())
        if total_var <= 0.0:
            raise SystemExit("Total variance is non-positive; check embeddings.")

        var_ratio = eigvals / total_var

        top = min(args.top, var_ratio.size)
        print(f"\nTop {top} principal components (variance ratios):")
        cum = 0.0
        for i in range(top):
            vr = float(var_ratio[i])
            cum += vr
            print(f"  PC{i+1:3d}: ratio={vr:7.5f}, cumulative={cum:7.5f}")

        # Report cumulative variance at a few candidate cutoffs.
        candidates = [32, 64, 128, 256]
        print("\nCumulative variance at candidate dimensions:")
        for d in candidates:
            if d > var_ratio.size:
                continue
            cum_d = float(var_ratio[:d].sum())
            print(f"  d={d:4d}: cumulative_variance={cum_d:7.5f}")

    finally:
        conn.close()


if __name__ == "__main__":  # pragma: no cover
    main()
