"""
Site Metrics — compute stage
----------------------------
Aggregates standardized trajectory CSVs per *site* (one folder = one site;
every ``*.csv`` inside the folder is pooled) and writes result tables to
``<out>/<site>/``. Plotting is a separate stage: feed one or more of those
result folders to ``plot_site_metrics.py``.

Metric definitions:

- **Speed**: the standardized ``speed`` column (m/s), all rows.
- **Density**: vehicles per km per frame. The roadway length is estimated
  per CSV as the 0.5–99.5 percentile span of positions projected on the
  first principal axis of all trajectory points.
- **Car-following TTC** (traditional 1-D TTC): same ``laneId``, follower
  behind leader along the lane direction (circular mean heading of the
  lane), bumper-to-bumper gap / closing speed, only when closing.
- **2D-TTC conflicts**: exact constant-velocity swept-rectangle time to
  first contact — separating-axis sweep of the two heading-aligned
  bounding boxes under the current relative velocity. A pair whose 2D-TTC
  drops below ``--ttc-threshold`` (default 3 s) is in conflict;
  consecutive conflict frames of the same pair are merged into one event,
  classified by heading geometry at the min-TTC frame into ``rear_end`` /
  ``side_swipe`` / ``angled`` / ``head_on`` (same category names as
  ``ssm_calculator``).

The per-CSV frame rate is inferred automatically from the median ratio of
``speed`` to per-frame displacement (override with ``--fps``).

Run (from anywhere):
    python standardized_data_toolkit/utils/compute_site_metrics.py \
        --site kzm6=/path/to/kzm6_folder \
        --site highd=/path/to/highd_folder \
        --out ./output/site_metrics
"""

from __future__ import annotations

import argparse
import glob
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_OUT_DIR = os.path.join(_REPO_ROOT, "output", "site_metrics")

REQUIRED_COLS = ["frameNum", "carId", "carCenterXm", "carCenterYm", "heading", "speed"]
OPTIONAL_COLS = ["laneId", "objClass"] + [f"boundingBox{i}{a}m" for i in (1, 2, 3, 4) for a in ("X", "Y")]

# Conflict categories — keep the ssm_calculator naming.
CONFLICT_TYPES = ["rear_end", "side_swipe", "angled", "head_on"]

SAME_DIRECTION_DEG = 30.0        # heading diff below this -> same direction
OPPOSITE_DIRECTION_DEG = 150.0   # heading diff above this -> opposing
LANE_ALIGN_DEG = 45.0            # follower/leader must align with lane direction
MIN_CLOSING_SPEED = 0.1          # m/s, below this a pair is not closing
SUMMARY_TTC_CAP = 60.0           # s, cf-TTC values above this are ignored in stats
SPEED_SAMPLE_CAP = 50_000        # rows kept in speed_samples.csv (plot input)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def discover_csvs(folder: str) -> List[str]:
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not files:
        raise FileNotFoundError(f"no *.csv files found in site folder: {folder}")
    return files


def load_tracks(csv_path: str, classes: Optional[Sequence[int]]) -> pd.DataFrame:
    header = pd.read_csv(csv_path, nrows=0).columns
    missing = [c for c in REQUIRED_COLS if c not in header]
    if missing:
        raise ValueError(f"{csv_path}: missing required columns {missing}")
    usecols = REQUIRED_COLS + [c for c in OPTIONAL_COLS if c in header]
    df = pd.read_csv(csv_path, usecols=usecols)
    if "laneId" not in df.columns:
        df["laneId"] = -1
    if classes is not None and "objClass" in df.columns:
        df = df[df["objClass"].isin(classes)].reset_index(drop=True)
    df["length"], df["width"] = _vehicle_dimensions(df)
    return df


def _vehicle_dimensions(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Per-row vehicle length/width from the bounding-box corners.

    Distances from corner 1 to corners 2/3/4 are the two edges plus the
    diagonal; length is the longer edge, width the shorter one. Taken from
    each car's first row (the footprint is constant per car).
    """
    bbox_cols = [f"boundingBox{i}{a}m" for i in (1, 2, 3, 4) for a in ("X", "Y")]
    if any(c not in df.columns for c in bbox_cols):
        n = len(df)
        return np.full(n, 4.5), np.full(n, 1.8)  # generic passenger-car fallback
    first = df.groupby("carId", sort=False).head(1)
    p = first[bbox_cols].to_numpy(float).reshape(-1, 4, 2)
    d = np.linalg.norm(p[:, 1:, :] - p[:, :1, :], axis=2)  # corner1 -> corners 2,3,4
    d.sort(axis=1)
    length = df["carId"].map(pd.Series(d[:, 1], index=first["carId"])).fillna(4.5).to_numpy()
    width = df["carId"].map(pd.Series(d[:, 0], index=first["carId"])).fillna(1.8).to_numpy()
    return length, width


def infer_fps(df: pd.DataFrame, max_cars: int = 100) -> float:
    """Median of speed / per-frame displacement over a sample of cars."""
    ratios = []
    for _, g in df.groupby("carId", sort=False):
        if len(g) < 20:
            continue
        g = g.sort_values("frameNum")
        step = np.diff(g["frameNum"].to_numpy())
        disp = np.hypot(np.diff(g["carCenterXm"].to_numpy()), np.diff(g["carCenterYm"].to_numpy()))
        sp = g["speed"].to_numpy()[:-1]
        ok = (step == 1) & (disp > 0.02) & (sp > 0.5)
        if ok.sum() >= 10:
            ratios.append(np.median(sp[ok] / disp[ok]))
        if len(ratios) >= max_cars:
            break
    if not ratios:
        return 25.0
    return float(np.round(np.median(ratios), 1))


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------
def compute_density(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Vehicles per km per frame; roadway length = principal-axis extent."""
    pts = df[["carCenterXm", "carCenterYm"]].to_numpy(float)
    if len(pts) > 100_000:
        pts = pts[np.random.default_rng(0).choice(len(pts), 100_000, replace=False)]
    centered = pts - pts.mean(axis=0)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    proj = df[["carCenterXm", "carCenterYm"]].to_numpy(float) @ vt[0]
    lo, hi = np.percentile(proj, [0.5, 99.5])
    extent_km = max(hi - lo, 1.0) / 1000.0
    counts = df.groupby("frameNum", sort=True).size()
    return pd.DataFrame(
        {
            "source": source,
            "frameNum": counts.index,
            "vehicle_count": counts.to_numpy(),
            "density_veh_per_km": counts.to_numpy() / extent_km,
        }
    )


def _circular_mean_deg(deg: pd.Series) -> float:
    rad = np.radians(deg.to_numpy(float))
    return float(np.degrees(np.arctan2(np.sin(rad).mean(), np.cos(rad).mean())))


def _angle_diff_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    d = np.abs(a - b) % 360.0
    return np.where(d > 180.0, 360.0 - d, d)


def compute_cf_ttc(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Traditional car-following TTC on same-lane follower/leader pairs."""
    sub = df[df["laneId"] >= 0].copy()
    if sub.empty:
        return pd.DataFrame()
    lane_dir = sub.groupby("laneId")["heading"].apply(_circular_mean_deg)
    sub["lane_dir"] = sub["laneId"].map(lane_dir)
    sub = sub[_angle_diff_deg(sub["heading"].to_numpy(), sub["lane_dir"].to_numpy()) <= LANE_ALIGN_DEG]
    if sub.empty:
        return pd.DataFrame()
    rad = np.radians(sub["lane_dir"].to_numpy())
    sub["s"] = sub["carCenterXm"].to_numpy() * np.cos(rad) + sub["carCenterYm"].to_numpy() * np.sin(rad)
    sub["v_along"] = sub["speed"].to_numpy() * np.cos(np.radians(sub["heading"].to_numpy()) - rad)

    sub = sub.sort_values(["frameNum", "laneId", "s"], kind="mergesort")
    grp = sub.groupby(["frameNum", "laneId"], sort=False)
    lead = {c: grp[c].shift(-1) for c in ("s", "v_along", "length", "carId")}
    gap = lead["s"] - sub["s"] - (lead["length"] + sub["length"]) / 2.0
    closing = sub["v_along"] - lead["v_along"]
    ok = lead["s"].notna() & (gap > 0) & (closing > MIN_CLOSING_SPEED)
    out = pd.DataFrame(
        {
            "source": source,
            "frameNum": sub.loc[ok, "frameNum"].to_numpy(),
            "laneId": sub.loc[ok, "laneId"].to_numpy(),
            "follower": sub.loc[ok, "carId"].to_numpy(),
            "leader": lead["carId"][ok].to_numpy(),
            "gap_m": gap[ok].round(3).to_numpy(),
            "closing_speed": closing[ok].round(3).to_numpy(),
        }
    )
    out["ttc"] = (out["gap_m"] / out["closing_speed"]).round(3)
    return out


_TRIU_CACHE: Dict[int, Tuple[np.ndarray, np.ndarray]] = {}


def _triu(n: int) -> Tuple[np.ndarray, np.ndarray]:
    if n not in _TRIU_CACHE:
        _TRIU_CACHE[n] = np.triu_indices(n, 1)
    return _TRIU_CACHE[n]


def _swept_obb_ttc(
    dp: np.ndarray, dv: np.ndarray, axes: np.ndarray, radii: np.ndarray, threshold: float
) -> np.ndarray:
    """Exact time to first contact of two moving oriented rectangles.

    Separating-axis sweep: on each of the 4 candidate axes the projected
    center gap is ``d + v t`` and the boxes touch while ``|d + v t| <= R``.
    The pair collides during the intersection of the 4 per-axis windows;
    2D-TTC is the entry time of that intersection (0 if already
    overlapping, inf if the windows never intersect at t >= 0).

    dp/dv: (P, 2); axes: (P, 4, 2); radii: (P, 4) summed projection radii.
    """
    d = np.einsum("pkc,pc->pk", axes, dp)
    v = np.einsum("pkc,pc->pk", axes, dv)
    still = np.abs(v) < 1e-9
    never = still & (np.abs(d) > radii)  # parallel gap on this axis never closes
    v_safe = np.where(still, 1.0, v)
    t1 = (-radii - d) / v_safe
    t2 = (radii - d) / v_safe
    lo = np.minimum(t1, t2)
    hi = np.maximum(t1, t2)
    lo[still] = -np.inf
    hi[still] = np.inf
    entry = lo.max(axis=1)
    exit_ = hi.min(axis=1)
    ttc = np.where(
        never.any(axis=1) | (entry > exit_) | (exit_ < 0), np.inf, np.maximum(entry, 0.0)
    )
    ttc[ttc >= threshold] = np.inf
    return ttc


def compute_2d_ttc_conflicts(
    df: pd.DataFrame,
    source: str,
    fps: float,
    threshold: float,
    max_pair_dist: float,
    frame_step: int,
) -> pd.DataFrame:
    """Per-frame pairwise swept-OBB 2D-TTC, merged into conflict events."""
    cols = ["frameNum", "carId", "carCenterXm", "carCenterYm", "heading", "speed", "length", "width"]
    data = df[cols].sort_values("frameNum", kind="mergesort")
    frames = data["frameNum"].to_numpy()
    boundaries = np.flatnonzero(np.diff(frames)) + 1
    starts = np.concatenate([[0], boundaries])
    ends = np.concatenate([boundaries, [len(frames)]])

    xy = data[["carCenterXm", "carCenterYm"]].to_numpy(float)
    hd = np.radians(data["heading"].to_numpy(float))
    u = np.stack([np.cos(hd), np.sin(hd)], axis=1)   # heading unit vector
    nrm = np.stack([-u[:, 1], u[:, 0]], axis=1)      # lateral unit vector
    vel = data["speed"].to_numpy(float)[:, None] * u
    hl = data["length"].to_numpy(float) / 2.0
    hw = data["width"].to_numpy(float) / 2.0
    ids = data["carId"].to_numpy()
    heading_deg = data["heading"].to_numpy(float)

    records = []
    for k in range(0, len(starts), frame_step):
        s, e = starts[k], ends[k]
        n = e - s
        if n < 2:
            continue
        iu, ju = _triu(n)
        gi, gj = iu + s, ju + s
        dp = xy[gj] - xy[gi]
        near = (dp * dp).sum(axis=1) < max_pair_dist * max_pair_dist
        if not near.any():
            continue
        gi, gj, dp = gi[near], gj[near], dp[near]
        axes = np.stack([u[gi], nrm[gi], u[gj], nrm[gj]], axis=1)  # (P, 4, 2)
        radii = (
            hl[gi, None] * np.abs(np.einsum("pkc,pc->pk", axes, u[gi]))
            + hw[gi, None] * np.abs(np.einsum("pkc,pc->pk", axes, nrm[gi]))
            + hl[gj, None] * np.abs(np.einsum("pkc,pc->pk", axes, u[gj]))
            + hw[gj, None] * np.abs(np.einsum("pkc,pc->pk", axes, nrm[gj]))
        )
        ttc = _swept_obb_ttc(dp, vel[gj] - vel[gi], axes, radii, threshold)
        conflict = np.isfinite(ttc)
        if not conflict.any():
            continue
        gi, gj = gi[conflict], gj[conflict]
        # canonical pair order (smaller id first) so events merge across frames
        # regardless of the row order inside each frame
        swap = ids[gi] > ids[gj]
        gi, gj = np.where(swap, gj, gi), np.where(swap, gi, gj)
        records.append(
            pd.DataFrame(
                {
                    "frameNum": frames[gi],
                    "id1": ids[gi],
                    "id2": ids[gj],
                    "ttc2d": ttc[conflict],
                    "x1": xy[gi, 0], "y1": xy[gi, 1], "x2": xy[gj, 0], "y2": xy[gj, 1],
                    "h1": heading_deg[gi], "h2": heading_deg[gj],
                }
            )
        )
    if not records:
        return pd.DataFrame()
    raw = pd.concat(records, ignore_index=True)
    return _merge_conflict_events(raw, source, fps, frame_step)


def _merge_conflict_events(raw: pd.DataFrame, source: str, fps: float, frame_step: int) -> pd.DataFrame:
    """Merge consecutive conflict frames of a pair into one event, classify it."""
    raw = raw.sort_values(["id1", "id2", "frameNum"], kind="mergesort").reset_index(drop=True)
    gap_tol = max(frame_step, int(round(0.5 * fps)))
    new_pair = (raw["id1"].ne(raw["id1"].shift())) | (raw["id2"].ne(raw["id2"].shift()))
    gap = raw["frameNum"].diff() > gap_tol
    raw["event"] = (new_pair | gap).cumsum()

    worst = raw.loc[raw.groupby("event")["ttc2d"].idxmin()].set_index("event")
    span = raw.groupby("event")["frameNum"].agg(["min", "max"])
    events = pd.DataFrame(
        {
            "source": source,
            "id1": worst["id1"],
            "id2": worst["id2"],
            "start_frame": span["min"],
            "end_frame": span["max"],
            "duration_s": ((span["max"] - span["min"]) / fps).round(3),
            "min_ttc2d": worst["ttc2d"].round(3),
            "conflict_type": _classify_conflicts(worst),
        }
    ).reset_index(drop=True)
    return events


def _classify_conflicts(worst: pd.DataFrame) -> np.ndarray:
    """Angle-based conflict typing at the min-TTC frame.

    heading diff > 150 deg -> head_on; 30..150 deg -> angled (crossing);
    < 30 deg (same direction): rear_end if the rear vehicle points at the
    front one (bearing < 30 deg), else side_swipe.
    """
    h1, h2 = worst["h1"].to_numpy(), worst["h2"].to_numpy()
    hdiff = _angle_diff_deg(h1, h2)
    h1r, h2r = np.radians(h1), np.radians(h2)
    # travel direction of the pair = mean heading; who is behind along it?
    mx, my = np.cos(h1r) + np.cos(h2r), np.sin(h1r) + np.sin(h2r)
    proj1 = worst["x1"].to_numpy() * mx + worst["y1"].to_numpy() * my
    proj2 = worst["x2"].to_numpy() * mx + worst["y2"].to_numpy() * my
    one_behind = proj1 < proj2
    bx = np.where(one_behind, worst["x2"] - worst["x1"], worst["x1"] - worst["x2"])
    by = np.where(one_behind, worst["y2"] - worst["y1"], worst["y1"] - worst["y2"])
    rear_heading = np.where(one_behind, h1, h2)
    bearing = _angle_diff_deg(np.degrees(np.arctan2(by, bx)), rear_heading)

    out = np.full(len(worst), "angled", dtype=object)
    out[hdiff > OPPOSITE_DIRECTION_DEG] = "head_on"
    same = hdiff < SAME_DIRECTION_DEG
    out[same & (bearing < SAME_DIRECTION_DEG)] = "rear_end"
    out[same & (bearing >= SAME_DIRECTION_DEG)] = "side_swipe"
    return out


# ---------------------------------------------------------------------------
# Site aggregation and table output
# ---------------------------------------------------------------------------
@dataclass
class SiteResult:
    name: str
    speed: np.ndarray = field(default_factory=lambda: np.array([]))
    density: pd.DataFrame = field(default_factory=pd.DataFrame)
    cf_ttc: pd.DataFrame = field(default_factory=pd.DataFrame)
    conflicts: pd.DataFrame = field(default_factory=pd.DataFrame)
    meta: List[dict] = field(default_factory=list)

    @property
    def conflict_counts(self) -> pd.Series:
        base = pd.Series(0, index=CONFLICT_TYPES, name="count")
        if not self.conflicts.empty:
            base = base.add(self.conflicts["conflict_type"].value_counts(), fill_value=0)
        return base.astype(int).reindex(CONFLICT_TYPES)


def process_site(name: str, folder: str, args: argparse.Namespace) -> SiteResult:
    result = SiteResult(name=name)
    speed_parts, density_parts, ttc_parts, conflict_parts = [], [], [], []
    for csv_path in discover_csvs(folder):
        source = os.path.splitext(os.path.basename(csv_path))[0]
        df = load_tracks(csv_path, args.classes)
        fps = args.fps if args.fps else infer_fps(df)
        print(f"  [{name}] {source}: {len(df):,} rows, {df['frameNum'].nunique():,} frames, fps={fps:g}")
        result.meta.append(
            {
                "site": name, "source": source, "rows": len(df),
                "frames": df["frameNum"].nunique(), "fps": fps,
                "ttc_threshold": args.ttc_threshold, "max_pair_dist": args.max_pair_dist,
                "frame_step": args.frame_step,
                "classes": "all" if args.classes is None else ";".join(map(str, args.classes)),
            }
        )
        speed_parts.append(df["speed"].to_numpy(float))
        density_parts.append(compute_density(df, source))
        ttc = compute_cf_ttc(df, source)
        if not ttc.empty:
            ttc_parts.append(ttc)
        conflicts = compute_2d_ttc_conflicts(
            df, source, fps, args.ttc_threshold, args.max_pair_dist, args.frame_step
        )
        if not conflicts.empty:
            conflict_parts.append(conflicts)
    result.speed = np.concatenate(speed_parts)
    result.density = pd.concat(density_parts, ignore_index=True)
    result.cf_ttc = pd.concat(ttc_parts, ignore_index=True) if ttc_parts else pd.DataFrame()
    result.conflicts = pd.concat(conflict_parts, ignore_index=True) if conflict_parts else pd.DataFrame()
    return result


def _summary_row(site: str, metric: str, values: np.ndarray) -> dict:
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return {"site": site, "metric": metric, "count": 0}
    q = np.percentile(values, [5, 25, 50, 75, 95])
    return {
        "site": site, "metric": metric, "count": len(values),
        "mean": round(float(values.mean()), 4), "std": round(float(values.std()), 4),
        "min": round(float(values.min()), 4), "p5": round(q[0], 4), "p25": round(q[1], 4),
        "median": round(q[2], 4), "p75": round(q[3], 4), "p95": round(q[4], 4),
        "max": round(float(values.max()), 4),
    }


def _distribution_table(values: np.ndarray, bins: np.ndarray) -> pd.DataFrame:
    counts, edges = np.histogram(values[np.isfinite(values)], bins=bins)
    widths = np.diff(edges)
    total = max(counts.sum(), 1)
    return pd.DataFrame(
        {
            "bin_left": edges[:-1].round(4),
            "bin_right": edges[1:].round(4),
            "count": counts,
            "pdf": (counts / total / widths).round(6),
        }
    )


def write_site_tables(result: SiteResult, out_dir: str) -> None:
    """Write all result tables for one site into ``<out_dir>/<site>/``."""
    site_dir = os.path.join(out_dir, result.name)
    os.makedirs(site_dir, exist_ok=True)
    metric_values = {
        "speed_mps": result.speed,
        "density_veh_per_km": result.density["density_veh_per_km"].to_numpy(float),
        "cf_ttc_s": (
            result.cf_ttc.loc[result.cf_ttc["ttc"] <= SUMMARY_TTC_CAP, "ttc"].to_numpy(float)
            if not result.cf_ttc.empty else np.array([])
        ),
        "min_ttc2d_s": (
            result.conflicts["min_ttc2d"].to_numpy(float) if not result.conflicts.empty else np.array([])
        ),
    }
    summary_rows = []
    for metric, values in metric_values.items():
        summary_rows.append(_summary_row(result.name, metric, values))
        if len(values) and metric != "min_ttc2d_s":
            bins = np.linspace(0, np.percentile(values, 99.5) * 1.05 + 1e-9, 61)
            _distribution_table(values, bins).to_csv(
                os.path.join(site_dir, f"{metric}_distribution.csv"), index=False
            )
    pd.DataFrame(summary_rows).to_csv(os.path.join(site_dir, "summary.csv"), index=False)
    pd.DataFrame(result.meta).to_csv(os.path.join(site_dir, "meta.csv"), index=False)

    speed = result.speed
    if len(speed) > SPEED_SAMPLE_CAP:  # plot input; a seeded subsample keeps the file small
        speed = np.random.default_rng(0).choice(speed, SPEED_SAMPLE_CAP, replace=False)
    pd.DataFrame({"speed": np.round(speed, 4)}).to_csv(
        os.path.join(site_dir, "speed_samples.csv"), index=False
    )
    result.density.to_csv(os.path.join(site_dir, "density_per_frame.csv"), index=False)
    if not result.cf_ttc.empty:
        result.cf_ttc.to_csv(os.path.join(site_dir, "cf_ttc_samples.csv"), index=False)
    if not result.conflicts.empty:
        result.conflicts.to_csv(os.path.join(site_dir, "conflict_events.csv"), index=False)
    result.conflict_counts.rename_axis("conflict_type").reset_index().to_csv(
        os.path.join(site_dir, "conflict_type_counts.csv"), index=False
    )
    print(f"  tables -> {site_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_site(spec: str) -> Tuple[str, str]:
    if "=" in spec:
        name, folder = spec.split("=", 1)
    else:
        name, folder = os.path.basename(os.path.normpath(spec)), spec
    if not os.path.isdir(folder):
        raise argparse.ArgumentTypeError(f"site folder not found: {folder}")
    return name, folder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--site", action="append", required=True, metavar="NAME=FOLDER",
                        help="site spec, repeatable; NAME=FOLDER or just FOLDER (name = basename)")
    parser.add_argument("--out", default=DEFAULT_OUT_DIR, help="output root; tables go to <out>/<site>/")
    parser.add_argument("--ttc-threshold", type=float, default=3.0, help="2D-TTC conflict threshold in s")
    parser.add_argument("--fps", type=float, default=None, help="override auto-inferred frame rate")
    parser.add_argument("--frame-step", type=int, default=1, help="frame subsampling for pairwise 2D-TTC")
    parser.add_argument("--max-pair-dist", type=float, default=100.0, help="pairwise distance cutoff in m")
    parser.add_argument("--classes", type=int, nargs="*", default=None,
                        help="keep only these objClass values (default: all)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    site_specs = [_parse_site(s) for s in args.site]
    for name, folder in site_specs:
        print(f"processing site '{name}' ({folder})")
        write_site_tables(process_site(name, folder, args), args.out)
    print(f"done. plot with: python {os.path.join(os.path.dirname(__file__), 'plot_site_metrics.py')} "
          + " ".join(f"--metrics {os.path.join(args.out, n)}" for n, _ in site_specs))


if __name__ == "__main__":
    main()
