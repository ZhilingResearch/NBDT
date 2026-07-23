# Utils

Standalone utility scripts that don't fit inside a specific processing module.

> The earlier loose helpers (`box_distance.py`, `data_loader.py`, `main.py`, `output_json.py`, `ssm.py`, `visualizer.py`) have been refactored into the class-based modules under [`ssm_calculator/`](../ssm_calculator/) (`GeometryHelper`, `TrackDataStore`, `InstantSSMCalculator`, `PeriodSSMCalculator`, etc.) and removed from this folder.

## Current scripts

- `visualize_waymo_trajectory.py` — animated GIF visualization of a Waymo Open Motion scenario, with the ego (SDC) highlighted
- `compute_site_metrics.py` + `plot_site_metrics.py` — two-stage per-site metric pipeline (speed / density / car-following TTC / 2D-TTC conflict types) over standardized trajectory CSVs; see [`site_metrics.md`](site_metrics.md)

---

## `compute_site_metrics.py` / `plot_site_metrics.py` — per-site metric pipeline

One folder = one site (all `*.csv` inside are pooled). The **compute** stage writes CSV result tables to `<out>/<site>/` (summary stats, distributions, per-frame density, cf-TTC samples, 2D-TTC conflict events and type counts). The **plot** stage reads any combination of computed site folders and draws a four-panel academic-style figure — three overlaid distribution curves plus a conflict-type bar chart — per site and/or as a multi-site comparison. All figure text is Arial at one font size.

Usage, parameters, metric definitions, and output-file reference: **[`site_metrics.md`](site_metrics.md)**.

```bash
python standardized_data_toolkit/utils/compute_site_metrics.py \
    --site kzm6=/path/to/kzm6_folder --site highd=/path/to/highd_folder
python standardized_data_toolkit/utils/plot_site_metrics.py \
    --metrics output/site_metrics/kzm6 --metrics output/site_metrics/highd
```

---

## `visualize_waymo_trajectory.py` — Waymo scenario animation

Renders one scenario from `data/waymo_ozone.csv` as a dark-themed animated GIF. Every agent is drawn as a heading-aligned bounding box with a fading motion trail, color-coded by object type. The Waymo ego vehicle (SDC) is auto-detected and highlighted with a red box, a halo, a longer trail, and a live speed label.

### Ego identification

The raw `waymo_ozone.csv` has no explicit `is_ego` column, but every scenario contains exactly one row-group with `obj_type=1` AND `vtype=2` — that is the SDC. All other vehicles have `vtype=1`. The script uses this rule internally.

Type encoding used by the script:

| `obj_type` | `vtype` | Drawn as |
|---|---|---|
| 1 | 1 | Vehicle (NPC, cyan) |
| **1** | **2** | **Ego / SDC (red, highlighted)** |
| 2 | 3 | Pedestrian (yellow) |
| 3 | 3 | Cyclist (pink) |

### Inputs & outputs

- **Input**: a CSV with columns `scenarioId, Frame, carId, obj_type, vtype, carCenterXm, carCenterYm, boundingBox{1..4}{X,Y}m, heading, speed`. Default path is `<repo root>/data/waymo_ozone.csv`.
- **Output**: an animated GIF (default `<repo root>/waymo_trajectory.gif`).

### Usage

```bash
# From the repo root, render an auto-picked medium-density scenario:
python standardized_data_toolkit/utils/visualize_waymo_trajectory.py

# List the top scenarios by agent count, so you can pick one:
python standardized_data_toolkit/utils/visualize_waymo_trajectory.py --list

# Render a specific scenario to a custom output path:
python standardized_data_toolkit/utils/visualize_waymo_trajectory.py \
    --scenario 2bc07893b2abbb07 \
    --out output/scenario_2bc07.gif

# Point at a different CSV:
python standardized_data_toolkit/utils/visualize_waymo_trajectory.py \
    --csv /path/to/other_waymo_ozone.csv
```

### CLI flags

| Flag | Default | Meaning |
|---|---|---|
| `--csv` | `<repo>/data/waymo_ozone.csv` | Input CSV path |
| `--scenario` | auto (≈80-agent scenario) | `scenarioId` to render |
| `--out` | `<repo>/waymo_trajectory.gif` | Output GIF path |
| `--list` | — | Print top scenarios by agent count and exit |

### Tuning

Tunable constants are defined at the top of the script: `TRAIL_LEN`, `EGO_TRAIL_LEN`, `FPS`, `DPI`, `PAD_M`, and the `TYPE_COLORS` palette.

### Dependencies

`pandas`, `numpy`, `matplotlib` (uses `PillowWriter` for GIF output, so no `ffmpeg` required).
