# -*- coding: utf-8 -*-
from __future__ import annotations

"""Inspect interest cluster quality inside clawsqlite.

This helper is similar in spirit to the radar-side scripts, but works
purely against the clawsqlite knowledge DB. It reconstructs the
"interest" vectors exactly as `build_interest_clusters` does, then
compares:

- per-cluster radius (mean/max distance of members to centroid)
- pairwise centroid distances
- simple silhouette-style scores

Usage (from clawsqlite repo root):

    MPLCONFIGDIR=/tmp/mplconfig \
    python -m tests.test_interest_cluster_quality \
      --db /path/to/clawkb.sqlite3 \
      --min-size 5 \
      --max-clusters 16

This is NOT a formal unit test; it's an analysis tool to decide whether
clusters are well-separated or "one big continuous blob".
"""

import argparse
import os
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import math
import numpy as np

from clawsqlite_knowledge.interest import _blob_to_floats, _squared_l2
from clawsqlite_knowledge.embed import _resolve_vec_dim
from clawsqlite_knowledge.db import _find_vec0_so

try:
    import matplotlib.pyplot as plt  # type: ignore
except Exception:  # pragma: no cover - plotting is optional
    plt = None


@dataclass
class Cluster:
    id: int
    label: str | None
    size: int
    centroid: np.ndarray


@dataclass
class Member:
    cluster_id: int
    vec: np.ndarray


def load_clusters(conn: sqlite3.Connection, vec_dim: int) -> Dict[int, Cluster]:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, label, size, summary_centroid FROM interest_clusters"
    )
    clusters: Dict[int, Cluster] = {}
    for cid, label, size, blob in cur.fetchall():
        if blob is None:
            continue
        vec = np.frombuffer(blob, dtype="float32")
        if vec.size != vec_dim:
            vec = np.frombuffer(blob, dtype="float64")
        if vec.size != vec_dim:
            continue
        vec = vec.astype("float32")
        clusters[int(cid)] = Cluster(
            id=int(cid),
            label=label,
            size=int(size),
            centroid=vec,
        )
    return clusters


def _load_interest_vectors(conn: sqlite3.Connection, dim: int) -> Dict[int, List[Member]]:
    """Rebuild interest vectors in the same way as build_interest_clusters.

    We re-run the SQL in build_interest_clusters to ensure we use the
    same article subset and the same summary/tag mixing weights.

    Returns a mapping: cluster_id -> list[Member].
    """

    cur = conn.cursor()

    # Load raw rows as in build_interest_clusters
    cur.execute(
        """
SELECT a.id AS id,
       sv.embedding AS summary_embedding,
       tv.embedding AS tag_embedding
FROM articles a
LEFT JOIN articles_vec sv ON sv.id = a.id
LEFT JOIN articles_tag_vec tv ON tv.id = a.id
WHERE a.deleted_at IS NULL
  AND a.summary IS NOT NULL AND trim(a.summary) != ''
        """
    )
    rows = cur.fetchall()

    # Same mixing weights as build_interest_clusters
    w_tag = float(os.environ.get("CLAWSQLITE_INTEREST_TAG_WEIGHT", "0.75") or 0.75)
    if w_tag < 0.0:
        w_tag = 0.0
    if w_tag > 1.0:
        w_tag = 1.0
    w_sum = 1.0 - w_tag

    # Build interest vectors and remember article_id -> vector
    points: Dict[int, np.ndarray] = {}
    for r in rows:
        article_id = int(r[0])
        sv_blob = r[1]
        tv_blob = r[2]
        if sv_blob is None and tv_blob is None:
            continue

        sv = _blob_to_floats(sv_blob, dim) if sv_blob is not None else None
        tv = _blob_to_floats(tv_blob, dim) if tv_blob is not None else None
        if sv is None and tv is not None:
            vec = np.array(tv, dtype="float32")
        elif tv is None and sv is not None:
            vec = np.array(sv, dtype="float32")
        else:
            arr = np.zeros(dim, dtype="float32")
            if w_sum > 0.0:
                arr += w_sum * np.array(sv, dtype="float32")
            if w_tag > 0.0:
                arr += w_tag * np.array(tv, dtype="float32")
            vec = arr

        points[article_id] = vec

    # Map articles to clusters via interest_cluster_members
    cur.execute(
        "SELECT cluster_id, article_id FROM interest_cluster_members"
    )
    by_cluster: Dict[int, List[Member]] = defaultdict(list)
    for cid, aid in cur.fetchall():
        cid = int(cid)
        aid = int(aid)
        vec = points.get(aid)
        if vec is None:
            continue
        by_cluster[cid].append(Member(cluster_id=cid, vec=vec))

    return by_cluster


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 1.0
    return 1.0 - float(np.dot(a, b) / (na * nb))


def main() -> None:
    ap = argparse.ArgumentParser(description="Inspect interest cluster quality (internal)")
    ap.add_argument("--db", required=True, help="Path to clawkb.sqlite3")
    ap.add_argument("--vec-dim", type=int, default=None, help="Embedding dimension (optional)")
    args = ap.parse_args()

    db_path = Path(args.db)
    if not db_path.is_file():
        raise SystemExit(f"DB not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    # Best-effort load vec0 extension, mirroring clawsqlite_knowledge.db
    try:
        conn.enable_load_extension(True)
        ext = os.environ.get("CLAWSQLITE_VEC_EXT") or _find_vec0_so()
        if ext and ext.lower() != "none":
            conn.load_extension(ext)
    except Exception:
        # For this analysis helper we don't hard-fail on vec0 issues.
        pass

    # Return rows as tuples
    conn.row_factory = None

    try:
        dim = args.vec_dim or _resolve_vec_dim()
        clusters = load_clusters(conn, vec_dim=dim)
        if not clusters:
            raise SystemExit("No interest_clusters found in DB")

        print(f"Loaded {len(clusters)} clusters from {db_path}")

        by_cluster = _load_interest_vectors(conn, dim=dim)

        # 1) Per-cluster radius stats
        print("\nPer-cluster radius (cosine distance to centroid):")
        for cid, cl in sorted(clusters.items()):
            members = by_cluster.get(cid) or []
            if not members:
                print(f"  cluster {cid:3d}: size={cl.size:4d}, (no members in mapping)")
                continue
            dists = [cosine_distance(cl.centroid, m.vec) for m in members]
            print(
                f"  cluster {cid:3d}: size={cl.size:4d}, "
                f"n_members={len(members):4d}, "
                f"mean_radius={np.mean(dists):.3f}, max_radius={np.max(dists):.3f}"
            )

        # 2) Pairwise centroid distances
        ids = sorted(clusters.keys())
        n = len(ids)
        dists = []
        for i in range(n):
            for j in range(i + 1, n):
                ci = clusters[ids[i]].centroid
                cj = clusters[ids[j]].centroid
                d = cosine_distance(ci, cj)
                dists.append(d)

        if dists:
            dists_sorted = sorted(dists)
            print("\nPairwise centroid cosine distances (1 - cos sim):")
            print(
                f"  min={dists_sorted[0]:.3f} max={dists_sorted[-1]:.3f} "
                f"median={dists_sorted[len(dists_sorted)//2]:.3f}"
            )
        else:
            print("\nNot enough clusters to compute pairwise distances.")

        # 3) Optional 2D scatter of centroids via PCA
        if plt is None:
            print("\nmatplotlib not available; skipping centroid scatter plot.")
            return

        X = np.stack([clusters[cid].centroid for cid in ids])
        X_centered = X - X.mean(axis=0, keepdims=True)
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
        X2 = X_centered @ Vt[:2].T

        xs = X2[:, 0]
        ys = X2[:, 1]

        fig, ax = plt.subplots(figsize=(8, 6))
        sc = ax.scatter(xs, ys, c=range(len(ids)), cmap="tab20", s=40)
        for i, cid in enumerate(ids):
            ax.text(xs[i], ys[i], str(cid), fontsize=8, ha="center", va="center")

        ax.set_title("Interest cluster centroids (PCA to 2D)")
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        fig.colorbar(sc, ax=ax, label="cluster index")
        fig.tight_layout()
        plt.show()

    finally:
        conn.close()


if __name__ == "__main__":  # pragma: no cover
    main()
