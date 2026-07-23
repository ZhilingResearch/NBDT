# Site Metrics — compute & plot

Two-stage pipeline over standardized trajectory CSVs. One folder = one site; every `*.csv` inside the folder is pooled into that site.

1. `compute_site_metrics.py` — computes the metrics and writes CSV tables to `<out>/<site>/`.
2. `plot_site_metrics.py` — reads any combination of computed site folders and draws the four-panel figure (speed / density / car-following TTC distribution curves + 2D-TTC conflict-type bars). Multiple sites are overlaid in one comparison figure.

## 1. Compute

```bash
python standardized_data_toolkit/utils/compute_site_metrics.py \
    --site kzm6=/path/to/kzm6_folder \
    --site highd=/path/to/highd_folder \
    --out ./output/site_metrics
```

| Flag | Default | Meaning |
|---|---|---|
| `--site` | required, repeatable | `NAME=FOLDER` (or just `FOLDER`, name = basename); all `*.csv` inside are pooled |
| `--out` | `<repo>/output/site_metrics` | output root; tables go to `<out>/<site>/` |
| `--ttc-threshold` | `3.0` | 2D-TTC conflict threshold (s) |
| `--fps` | auto per CSV | frame-rate override (auto = median of `speed` / per-frame displacement) |
| `--frame-step` | `1` | frame subsampling for the pairwise 2D-TTC pass |
| `--max-pair-dist` | `100.0` | pairwise distance cutoff (m) |
| `--classes` | all | keep only these `objClass` values |

Output tables per site (`<out>/<site>/`):

| File | Content |
|---|---|
| `summary.csv` | count / mean / std / percentiles per metric |
| `meta.csv` | per-source rows, frames, inferred fps, parameters used |
| `speed_samples.csv` | speed samples (subsampled to 50 k; plot input) |
| `density_per_frame.csv` | per-frame vehicle count and density (veh/km) |
| `cf_ttc_samples.csv` | car-following TTC samples (follower, leader, gap, closing speed, TTC) |
| `conflict_events.csv` | one row per conflict event (pair, frames, duration, min 2D-TTC, type) |
| `conflict_type_counts.csv` | event count per conflict type |
| `*_distribution.csv` | binned distribution (bin edges, count, pdf) of speed / density / cf-TTC |

## 2. Plot

```bash
# Per-site figures + one comparison figure overlaying the given sites:
python standardized_data_toolkit/utils/plot_site_metrics.py \
    --metrics ./output/site_metrics/kzm6 \
    --metrics ./output/site_metrics/highd \
    --out ./output/site_metrics
```

| Flag | Default | Meaning |
|---|---|---|
| `--metrics` | required, repeatable | computed site folder from stage 1; `NAME=FOLDER` or just `FOLDER` |
| `--out` | `<repo>/output/site_metrics` | output directory for figures |
| `--combined-only` | off | skip per-site figures, draw only the comparison figure |
| `--ttc-plot-max` | `15.0` | x-axis cap of the TTC panel (s) |
| `--font-size` | `11` | font size for all figure text (Arial everywhere) |
| `--dpi` | `300` | figure resolution |

Figures: `<site>_metrics.png` per site, plus `<name1>_<name2>_comparison.png` when more than one `--metrics` is given (semi-transparent overlaid distributions, grouped bars).

## Metric definitions

- **Speed** — the standardized `speed` column (m/s), all rows.
- **Density** — vehicles per km per frame; roadway length = 0.5–99.5 percentile span of positions projected on the first principal axis (per CSV).
- **Car-following TTC** — same `laneId`, follower behind leader along the lane direction (circular mean heading), bumper-to-bumper gap / closing speed, closing pairs only.
- **2D-TTC conflicts** — exact constant-velocity swept-rectangle time to first contact (separating-axis sweep of the two heading-aligned bounding boxes). TTC below the threshold → conflict; consecutive conflict frames of a pair merge into one event, classified at the min-TTC frame as `rear_end` / `side_swipe` / `angled` / `head_on`.

## Input requirements

Required columns: `frameNum`, `carId`, `carCenterXm`, `carCenterYm`, `heading`, `speed`. Optional: `laneId` (needed for car-following TTC), `objClass`, `boundingBox{1..4}{X,Y}m` (vehicle footprint; falls back to 4.5 m × 1.8 m).

Dependencies: `pandas`, `numpy`, `scipy`, `matplotlib`.
