"""
Site Metrics — plot stage
-------------------------
Reads result folders written by ``compute_site_metrics.py`` (one folder per
site) and draws the four-panel figure: speed / density / car-following TTC
distribution curves plus a 2D-TTC conflict-type bar chart.

Any combination of previously computed sites can be plotted together —
pass several ``--metrics`` folders and they are overlaid in one comparison
figure (semi-transparent distributions, grouped bars). All figure text is
Arial at one font size.

Run (from anywhere):
    python standardized_data_toolkit/utils/plot_site_metrics.py \
        --metrics ./output/site_metrics/kzm6 \
        --metrics ./output/site_metrics/highd \
        --out ./output/site_metrics
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from compute_site_metrics import CONFLICT_TYPES, DEFAULT_OUT_DIR

CONFLICT_LABELS = {"rear_end": "Rear-end", "side_swipe": "Side-swipe", "angled": "Angled", "head_on": "Head-on"}

# Fixed-order categorical palette (colorblind-validated); sites take slots in order.
SITE_PALETTE = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]

DEFAULT_FONT_SIZE = 11  # single size for every text element in the figures
KDE_MAX_SAMPLES = 30_000
KDE_GRID_POINTS = 256


# ---------------------------------------------------------------------------
# Loading computed site results
# ---------------------------------------------------------------------------
@dataclass
class SiteData:
    name: str
    speed: np.ndarray = field(default_factory=lambda: np.array([]))
    density: np.ndarray = field(default_factory=lambda: np.array([]))
    cf_ttc: np.ndarray = field(default_factory=lambda: np.array([]))
    conflict_counts: pd.Series = field(
        default_factory=lambda: pd.Series(0, index=CONFLICT_TYPES, dtype=int)
    )


def _read_column(site_dir: str, filename: str, column: str) -> np.ndarray:
    path = os.path.join(site_dir, filename)
    if not os.path.isfile(path):
        return np.array([])
    return pd.read_csv(path, usecols=[column])[column].to_numpy(float)


def load_site(name: str, site_dir: str) -> SiteData:
    data = SiteData(name=name)
    data.speed = _read_column(site_dir, "speed_samples.csv", "speed")
    data.density = _read_column(site_dir, "density_per_frame.csv", "density_veh_per_km")
    data.cf_ttc = _read_column(site_dir, "cf_ttc_samples.csv", "ttc")
    counts_path = os.path.join(site_dir, "conflict_type_counts.csv")
    if os.path.isfile(counts_path):
        counts = pd.read_csv(counts_path).set_index("conflict_type")["count"]
        data.conflict_counts = counts.reindex(CONFLICT_TYPES).fillna(0).astype(int)
    return data


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
def _apply_style(font_size: int) -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": font_size,
            "axes.titlesize": font_size,
            "axes.labelsize": font_size,
            "xtick.labelsize": font_size,
            "ytick.labelsize": font_size,
            "legend.fontsize": font_size,
            "figure.titlesize": font_size,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#52514e",
            "axes.labelcolor": "#0b0b0b",
            "axes.linewidth": 0.8,
            "xtick.color": "#52514e",
            "ytick.color": "#52514e",
            "xtick.labelcolor": "#0b0b0b",
            "ytick.labelcolor": "#0b0b0b",
            "axes.grid": True,
            "grid.color": "#d9d9d8",
            "grid.linewidth": 0.6,
            "axes.axisbelow": True,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _kde_curve(values: np.ndarray, lo: float, hi: float) -> Tuple[np.ndarray, np.ndarray]:
    from scipy.stats import gaussian_kde

    values = values[np.isfinite(values)]
    values = values[(values >= lo) & (values <= hi)]
    grid = np.linspace(lo, hi, KDE_GRID_POINTS)
    if len(values) < 10:
        return grid, np.zeros_like(grid)
    if len(values) > KDE_MAX_SAMPLES:
        values = np.random.default_rng(0).choice(values, KDE_MAX_SAMPLES, replace=False)
    if np.ptp(values) < 1e-9:
        return grid, np.zeros_like(grid)
    return grid, gaussian_kde(values)(grid)


def _plot_distributions(ax: plt.Axes, sites: List[SiteData], getter: Callable[[SiteData], np.ndarray],
                        xlabel: str, title: str, hi_cap: Optional[float] = None) -> None:
    pooled = [v for r in sites for v in [getter(r)] if len(v)]
    if not pooled:
        ax.set_title(title, loc="left")
        return
    hi = max(np.percentile(v[np.isfinite(v)], 99.5) for v in pooled) * 1.05
    if hi_cap is not None:
        hi = min(hi, hi_cap)
    for idx, r in enumerate(sites):
        values = getter(r)
        if not len(values):
            continue
        color = SITE_PALETTE[idx % len(SITE_PALETTE)]
        grid, dens = _kde_curve(values, 0.0, hi)
        ax.plot(grid, dens, color=color, linewidth=1.6, label=r.name)
        ax.fill_between(grid, dens, color=color, alpha=0.22, linewidth=0)
    ax.set_xlim(0, hi)
    ax.set_ylim(bottom=0)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Probability density")
    ax.set_title(title, loc="left")
    ax.grid(axis="x", visible=False)


def _plot_conflict_bars(ax: plt.Axes, sites: List[SiteData], title: str, font_size: int) -> None:
    n = len(sites)
    x = np.arange(len(CONFLICT_TYPES))
    width = 0.8 / n
    for idx, r in enumerate(sites):
        counts = r.conflict_counts.to_numpy()
        pos = x + (idx - (n - 1) / 2) * width
        color = SITE_PALETTE[idx % len(SITE_PALETTE)]
        ax.bar(pos, counts, width=width * 0.94, color=color, label=r.name,
               edgecolor="white", linewidth=0.8)
        for px, cnt in zip(pos, counts):
            ax.annotate(f"{cnt:,}", (px, cnt), ha="center", va="bottom",
                        xytext=(0, 1.5), textcoords="offset points", fontsize=font_size)
    ax.set_xticks(x)
    ax.set_xticklabels([CONFLICT_LABELS[t] for t in CONFLICT_TYPES])
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True, nbins=6))
    ax.set_ylabel("Event count")
    ax.set_ylim(0, max(1, max(r.conflict_counts.max() for r in sites)) * 1.18)
    ax.set_title(title, loc="left")
    ax.grid(axis="x", visible=False)


def plot_four_panel(sites: List[SiteData], out_path: str, dpi: int, ttc_plot_max: float,
                    font_size: int) -> None:
    _apply_style(font_size)
    fig, axes = plt.subplots(2, 2, figsize=(8.6, 6.4))
    _plot_distributions(axes[0, 0], sites, lambda r: r.speed, "Speed (m/s)", "(a) Speed")
    _plot_distributions(axes[0, 1], sites, lambda r: r.density, "Density (veh/km)", "(b) Density")
    _plot_distributions(axes[1, 0], sites, lambda r: r.cf_ttc, "TTC (s)", "(c) Car-following TTC",
                        hi_cap=ttc_plot_max)
    _plot_conflict_bars(axes[1, 1], sites, "(d) Conflict types", font_size)
    if len(sites) > 1:
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", ncol=len(sites), frameon=False,
                   bbox_to_anchor=(0.5, 1.0))
        fig.tight_layout(rect=(0, 0, 1, 0.95))
    else:
        fig.suptitle(sites[0].name, x=0.02, ha="left")
        fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    print(f"  figure -> {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_metrics(spec: str) -> Tuple[str, str]:
    if "=" in spec:
        name, folder = spec.split("=", 1)
    else:
        name, folder = os.path.basename(os.path.normpath(spec)), spec
    if not os.path.isdir(folder):
        raise argparse.ArgumentTypeError(f"metrics folder not found: {folder}")
    return name, folder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--metrics", action="append", required=True, metavar="NAME=FOLDER",
                        help="computed site folder (from compute_site_metrics.py), repeatable; "
                             "NAME=FOLDER or just FOLDER (name = basename)")
    parser.add_argument("--out", default=DEFAULT_OUT_DIR, help="output directory for figures")
    parser.add_argument("--combined-only", action="store_true",
                        help="skip per-site figures, draw only the comparison figure")
    parser.add_argument("--ttc-plot-max", type=float, default=15.0, help="x-axis cap for the TTC panel in s")
    parser.add_argument("--font-size", type=int, default=DEFAULT_FONT_SIZE, help="font size for all figure text")
    parser.add_argument("--dpi", type=int, default=300, help="figure resolution")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    specs = [_parse_metrics(s) for s in args.metrics]
    os.makedirs(args.out, exist_ok=True)
    sites = [load_site(name, folder) for name, folder in specs]
    if not args.combined_only:
        for site in sites:
            plot_four_panel([site], os.path.join(args.out, f"{site.name}_metrics.png"),
                            args.dpi, args.ttc_plot_max, args.font_size)
    if len(sites) > 1:
        name = "_".join(s.name for s in sites) if len(sites) <= 4 else "sites"
        plot_four_panel(sites, os.path.join(args.out, f"{name}_comparison.png"),
                        args.dpi, args.ttc_plot_max, args.font_size)
    print(f"done. figures in {args.out}")


if __name__ == "__main__":
    main()
