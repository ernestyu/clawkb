# -*- coding: utf-8 -*-
from __future__ import annotations

"""Suggest an interest merge distance based on current clusters.

This helper inspects the existing interest_clusters in a KB and
suggests a value for CLAWSQLITE_INTEREST_MERGE_DISTANCE based on the
median cluster radius.

It is intentionally a tests/ helper (not a public CLI subcommand).
"""

import argparse
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np

from clawsqlite_knowledge.db import _find_vec0_so
from clawsqlite_knowledge.embed import _resolve_vec_dim
from clawsqlite_knowledge.interest import _blob_to_floats


@dataclass
class Cluster:
    id: int
    size: int
    centroid: np.ndarray


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        return 1.0
    return 1.0 - float(np.dot(a, b) / (na * nb))


def _load_clusters(conn: sqlite3.Connection, dim: int) -> Dict[int, Cluster]:
    cur = conn.cursor()
    cur.execute("SELECT id, size, summary_centroid FROM interest_clusters")
    clusters: Dict[int, Cluster] = {}
    for cid, size, blob in cur.fetchall():
        if blob is None:
            continue
        # Try float32 then float64, mirroring other helpers.
        vec = np.frombuffer(blob, dtype="float32")
        if vec.size != dim:
            vec = np.frombuffer(blob, dtype="float64")
        if vec.size != dim:
            continue
        vec = vec.astype("float32")
        clusters[int(cid)] = Cluster(id=int(cid), size=int(size), centroid=vec)
    return clusters


def _load_interest_vectors(conn: sqlite3.Connection, dim: int) -> Dict[int, List[np.ndarray]]:
    """Rebuild interest vectors as in build_interest_clusters.

    Returns cluster_id -> list[vec].
    """
    cur = conn.cursor()
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

    article_vecs: Dict[int, np.ndarray] = {}
    for r in rows:
        aid = int(r[0])
        sv_blob = r[1]
        tv_blob = r[2]
        if sv_blob is None and tv_blob is None:
            continue
        try:
            sv = _blob_to_floats(sv_blob, dim) if sv_blob is not None else None
            tv = _blob_to_floats(tv_blob, dim) if tv_blob is not None else None
        except Exception:
            continue

        if sv is None and tv is not None:
            vec = np.asarray(tv, dtype="float32")
        elif tv is None and sv is not None:
            vec = np.asarray(sv, dtype="float32")
        else:
            arr = np.zeros(dim, dtype="float32")
            if w_sum > 0.0:
                arr += w_sum * np.asarray(sv, dtype="float32")
            if w_tag > 0.0:
                arr += w_tag * np.asarray(tv, dtype="float32")
            vec = arr
        article_vecs[aid] = vec

    cur.execute("SELECT cluster_id, article_id FROM interest_cluster_members")
    by_cluster: Dict[int, List[np.ndarray]] = {}
    for cid, aid in cur.fetchall():
        aid = int(aid)
        cid = int(cid)
        v = article_vecs.get(aid)
        if v is None:
            continue
        by_cluster.setdefault(cid, []).append(v)
    return by_cluster


def main() -> None:
    ap = argparse.ArgumentParser(description="Suggest CLAWSQLITE_INTEREST_MERGE_DISTANCE based on existing clusters")
    ap.add_argument("--db", required=True, help="Path to clawkb.sqlite3")
    ap.add_argument("--vec-dim", type=int, default=None, help="Embedding dimension (optional)")
    ap.add_argument("--alpha", type=float, default=0.4, help="Multiplier for median mean_radius")
    args = ap.parse_args()

    db_path = Path(args.db)
    if not db_path.is_file():
        raise SystemExit(f"DB not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        # Best-effort vec0 load, mirroring other helpers.
        try:
            conn.enable_load_extension(True)
            ext = os.environ.get("CLAWSQLITE_VEC_EXT") or _find_vec0_so()
            if ext and ext.lower() != "none":
                conn.load_extension(ext)
        except Exception:
            pass

        conn.row_factory = None

        dim = args.vec_dim or _resolve_vec_dim()
        clusters = _load_clusters(conn, dim=dim)
        if not clusters:
            raise SystemExit("No interest_clusters found in DB")

        by_cluster_vecs = _load_interest_vectors(conn, dim=dim)

        # Compute per-cluster mean radii.
        mean_radii: List[float] = []
        print("Per-cluster radius (for merge suggestion):")
        for cid in sorted(clusters.keys()):
            c = clusters[cid]
            vecs = by_cluster_vecs.get(cid) or []
            if not vecs:
                print(f"  cluster {cid:3d}: size={c.size:4d}, (no member vectors)")
                continue
            dists = [_cosine_distance(c.centroid, v) for v in vecs]
            m = float(np.mean(dists))
            mx = float(np.max(dists))
            mean_radii.append(m)
            print(
                f"  cluster {cid:3d}: size={c.size:4d}, n_members={len(vecs):4d}, "
                f"mean_radius={m:.3f}, max_radius={mx:.3f}"
            )

        if not mean_radii:
            raise SystemExit("Could not compute mean radii (no members)")

        mean_radii_sorted = sorted(mean_radii)
        median_radius = float(np.median(mean_radii_sorted))
        avg_radius = float(np.mean(mean_radii_sorted))

        # Suggest a merge distance as alpha * median_radius, with a safety clamp.
        raw_suggest = args.alpha * median_radius
        merge_suggest = max(0.01, min(0.30, raw_suggest))

        print("\nRadius summary:")
        print(f"  mean(mean_radius)   = {avg_radius:.3f}")
        print(f"  median(mean_radius) = {median_radius:.3f}")

        print("\nSuggested CLAWSQLITE_INTEREST_MERGE_DISTANCE:")
        print(f"  alpha        = {args.alpha:.3f}")
        print(f"  raw_suggest  = {raw_suggest:.3f}")
        print(f"  clamped      = {merge_suggest:.3f}")
        print("\nYou can apply this in your environment or .env as:")
        print(f"  export CLAWSQLITE_INTEREST_MERGE_DISTANCE={merge_suggest:.3f}")
    finally:
        conn.close()


if __name__ == "__main__":  # pragma: no cover
    main()
