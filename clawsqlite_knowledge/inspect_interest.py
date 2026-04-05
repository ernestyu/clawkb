# -*- coding: utf-8 -*-
"""Interest cluster inspection helpers (PCA plot + radius stats).

This module exposes the same logic as tests.test_interest_cluster_quality
but in a reusable form for the knowledge CLI.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np

from .embed import _resolve_vec_dim
from .db import _find_vec0_so
from .interest import load_interest_vectors_from_db

try:  # optional plotting
    import matplotlib.pyplot as plt  # type: ignore
except Exception:  # pragma: no cover
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


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 1.0
    return 1.0 - float(np.dot(a, b) / (na * nb))


def _load_clusters(conn: sqlite3.Connection, vec_dim: int) -> Dict[int, Cluster]:
    cur = conn.cursor()
    cur.execute("SELECT id, label, size, summary_centroid FROM interest_clusters")
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
    """Rebuild interest vectors in the same way as build_interest_clusters."""
    from collections import defaultdict

    article_ids, vectors_1024, _ = load_interest_vectors_from_db(conn, dim=dim)
    points: Dict[int, np.ndarray] = {
        int(aid): np.asarray(vec, dtype="float32")
        for aid, vec in zip(article_ids, vectors_1024)
    }

    cur = conn.cursor()
    cur.execute("SELECT cluster_id, article_id FROM interest_cluster_members")
    by_cluster: Dict[int, List[Member]] = defaultdict(list)
    for cid, aid in cur.fetchall():
        cid = int(cid)
        aid = int(aid)
        vec = points.get(aid)
        if vec is None:
            continue
        by_cluster[cid].append(Member(cluster_id=cid, vec=vec))
    return by_cluster


def inspect_interest_clusters(db_path: str, *, vec_dim: int | None = None, no_plot: bool = False) -> None:
    """Print interest cluster radius stats and optionally save a PCA PNG.

    This mirrors tests.test_interest_cluster_quality but is wired for CLI
    use. The PNG is written to the current working directory as
    ``interest_clusters_pca.png`` when plotting is enabled.
    """
    p = Path(db_path)
    if not p.is_file():
        raise SystemExit(f"DB not found: {db_path}")

    conn = sqlite3.connect(str(p))
    try:
        # Best-effort load vec0 extension, mirroring other helpers.
        try:
            conn.enable_load_extension(True)
            ext = os.environ.get("CLAWSQLITE_VEC_EXT") or _find_vec0_so()
            if ext and ext.lower() != "none":
                conn.load_extension(ext)
        except Exception:
            pass

        conn.row_factory = None

        dim = vec_dim or _resolve_vec_dim()
        clusters = _load_clusters(conn, vec_dim=dim)
        if not clusters:
            print("No interest_clusters found in DB")
            return

        print(f"Loaded {len(clusters)} clusters from {db_path}")

        by_cluster = _load_interest_vectors(conn, dim=dim)

        # 1) Per-cluster radius stats
        print("\nPer-cluster radius (cosine distance to centroid):")
        mean_radii: List[float] = []
        for cid in sorted(clusters.keys()):
            cl = clusters[cid]
            members = by_cluster.get(cid) or []
            if not members:
                print(f"  cluster {cid:3d}: size={cl.size:4d}, (no members in mapping)")
                continue
            dists = [_cosine_distance(cl.centroid, m.vec) for m in members]
            mean_r = float(np.mean(dists))
            mx = float(np.max(dists))
            mean_radii.append(mean_r)
            print(
                f"  cluster {cid:3d}: size={cl.size:4d}, "
                f"n_members={len(members):4d}, "
                f"mean_radius={mean_r:.3f}, max_radius={mx:.3f}"
            )

        # 2) Pairwise centroid distances
        ids = sorted(clusters.keys())
        n = len(ids)
        dists = []
        for i in range(n):
            for j in range(i + 1, n):
                ci = clusters[ids[i]].centroid
                cj = clusters[ids[j]].centroid
                d = _cosine_distance(ci, cj)
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

        if no_plot:
            return

        if plt is None:
            print("\nmatplotlib not available; skipping centroid scatter plot.")
            return

        # 3) PCA scatter of centroids with size/color encoding.
        X = np.stack([clusters[cid].centroid for cid in ids])
        X_centered = X - X.mean(axis=0, keepdims=True)
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
        X2 = X_centered @ Vt[:2].T

        xs = X2[:, 0]
        ys = X2[:, 1]

        sizes = []
        mean_radii_plot = []
        for cid in ids:
            cl = clusters[cid]
            members = by_cluster.get(cid) or []
            if members:
                dists = [_cosine_distance(cl.centroid, m.vec) for m in members]
                mean_r = float(np.mean(dists))
            else:
                mean_r = 0.0
            sizes.append(cl.size)
            mean_radii_plot.append(mean_r)

        sizes_arr = np.array(sizes, dtype="float32")
        if sizes_arr.size > 0:
            sizes_plot = 40.0 * np.sqrt(sizes_arr / sizes_arr.max())
        else:
            sizes_plot = 40.0

        fig, ax = plt.subplots(figsize=(8, 6))
        sc = ax.scatter(xs, ys, s=sizes_plot, c=mean_radii_plot, cmap="viridis")
        for i, cid in enumerate(ids):
            ax.text(xs[i], ys[i], str(cid), fontsize=8, ha="center", va="center")

        ax.set_title("Interest cluster centroids (PCA to 2D; size=size, color=mean_radius)")
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        cbar = fig.colorbar(sc, ax=ax, label="mean_radius (1 - cos)")
        cbar.ax.set_ylabel("mean_radius (1 - cos)", rotation=90, labelpad=10)
        fig.tight_layout()

        out_path = Path.cwd() / "interest_clusters_pca.png"
        fig.savefig(out_path, dpi=150)
        print(f"\nSaved centroid scatter plot to {out_path}")

    finally:
        conn.close()
