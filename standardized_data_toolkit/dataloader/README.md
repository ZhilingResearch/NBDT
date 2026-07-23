
# Standardized Data Transformation


## Data Transfer Tools

This module converts raw trajectory datasets into the NBDT standard format.

### Supported Datasets

- `highD`
- `inD`
- `NGSIM`
- `CitySim`
- `Waymo`
- `Lyft`
- `OpenACC`
- `ADAS_single`
- `ADAS_two_vehicle`

Set up your Python environment first.

Install the dependencies required by this project before running any transfer scripts.
```
pip intsall -r requirements.txt
```

### Start transfer current dataset into standard

Follow these steps:

1. Go to the `dataloader` directory.

```bash
cd dataloader
```

2. Run the transfer script with CLI arguments.

```bash
python factory.py --dataset highD --data_folder ./original_data --save_folder ./processed_data
```

- `--dataset` (`str`, default: `highD`)
  - Dataset key (case-sensitive): `highD`, `inD`, `rounD`, `NGSIM`, `CitySim`, `Waymo`, `Lyft`, `OpenACC`, `ADAS_single`, `ADAS_two_vehicle`
- `--data_folder` (`str`, default: `./original_data`)
  - Folder containing raw input files
- `--save_folder` (`str`, default: `./processed_data`)
  - Folder where converted CSV files are written
- `--use_yml` (`str`, default: `./config/config.yaml`)
  - YAML file loaded after CLI parsing; values in YAML override CLI/default values

3. If you prefer configuration files, use YAML from `config`.

```bash
python factory.py --use_yml ./config/config.yaml
```

- Example Config (`config/config.yaml`)

```yaml
dataset: highD
data_folder: ./original_data
save_folder: ./processed_data
```


#### Notes on `Waymo` (Waymo Motion Dataset)

Waymo Motion has no per-frame `lane_id` and no closed lane polygons, so
`laneId` is obtained by **centerline matching**: each vehicle centre is
projected onto every `LaneCenter.polyline` and assigned the nearest lane
within 2 m (else `-1`). Input is one or more `*.tfrecord` shards; requires
`tensorflow` and `waymo-open-dataset`.

`objClass` mapping (NBDT standard):

| Waymo `obj_type` | Label       | `objClass` |
|-----------------|-------------|-----------|
| 1               | VEHICLE     | 0 (car / generic vehicle) |
| 2               | PEDESTRIAN  | 5 |
| 3               | CYCLIST     | 4 |
| 0 / 4           | UNSET/OTHER | -1 |

> Waymo does not subdivide VEHICLE into car / taxi / truck / bus, so all
> VEHICLE agents are mapped to `objClass=0`. AV vs HDV is indicated by the
> extra `vtype` column (see **AV / HDV Indicator Columns** below).

Extra columns beyond the standard NBDT schema:

- `scenarioId` — Waymo scenario id (one TFRecord shard contains many scenarios)
- `tfFile` — source TFRecord filename
- `velocity_x`, `velocity_y` — per-frame velocity components (m/s) from Waymo state
- `length`, `width` — per-frame vehicle dimensions (m)
- `obj_type` — raw Waymo agent type: 0=UNSET, 1=VEHICLE, 2=PEDESTRIAN, 3=CYCLIST, 4=OTHER
- `vehicleRole` — unified AV/HDV indicator: 0=non-vehicle agent, 1=HDV, 2=AV/ego (see **AV / HDV Indicator Column** below)

---

#### Notes on `Lyft` (Lyft Level-5 Prediction Dataset)

> **Data availability**: The Lyft Level-5 dataset is no longer available for
> public download from the official source. Raw zarr archives must be obtained
> from parties who already hold them. Requires `l5kit` (`pip install l5kit`).

Expected directory layout under `--data_folder` (= `L5KIT_DATA_FOLDER`):

```
<data_folder>/
    <name>.zarr/          ← one or more zarr scene archives
    semantic_map/
        semantic_map.pb
        meta.json
```

```bash
python factory.py --dataset Lyft --data_folder /path/to/lyft_root --save_folder ./processed_data
```

Optional YAML config keys:

```yaml
dataset: Lyft
data_folder: /path/to/lyft_root
save_folder: ./processed_data
cfg_path: /path/to/lyft_map_config.yaml   # default: <data_folder>/lyft_map_config.yaml
num_scenes: 100                           # default: all scenes in the zarr
```

`objClass` mapping (NBDT standard):

| Lyft perception label | `objClass` |
|-----------------------|-----------|
| CAR, VAN              | 0 |
| BUS                   | 2 |
| TRUCK                 | 3 |
| MOTORCYCLE, MOTORCYCLIST | 4 |
| PEDESTRIAN            | 5 |
| other / unknown       | -1 |

Extra columns beyond the standard NBDT schema:

- `vehicleRole` — unified AV/HDV indicator: 0=surrounding agent, 2=AV/ego (see **AV / HDV Indicator Column** below)

Lyft provides no GPS data; `carCenterLon` and `carCenterLat` are always `-1`.
Pixel coordinates (`carCenterX/Y`, `boundingBox*X/Y`) are also `-1` because
the dataset supplies only metric world coordinates.

---

#### Notes on `ADAS_single` (FHWA ADAS Single-Vehicle, Central Ohio)

The FHWA naturalistic dataset arrives as one large appended CSV. The converter
streams it in chunks and groups rows into **field collections** keyed by
`date`, `time of day`, and route start/end. Each collection becomes one numbered
sub-folder under `--save_folder`, named
`{corridor}_{YYYYMMDD}_{HHMMSS}_run{run}_sub{sub}`, holding `metadata.csv`
(one row) and `trajectory.csv`. A `recordings_index.csv` at the root lists all
collections.

```bash
python factory.py --dataset ADAS_single --data_folder ./original_data/ADAS --save_folder ./processed_data/ADAS_single
```

Optional keys: `csv_path` (explicit source CSV), `test_run`, `test_sub_run`
(filter one run for a smoke test).

The source stores positions in a local map frame (meters). These map directly to
`carCenterXm` / `carCenterYm`; `carCenterLon` / `carCenterLat` are reconstructed
from `map_origin` using a local tangent-plane approximation. Pixel coordinates
(`carCenterX/Y`, `boundingBox*X/Y`) are `-1`. Output frame rate is 10 Hz.

`objClass` is inferred from vehicle length: longer than 10 m maps to `3` (truck),
otherwise `0` (car).

Extra trajectory columns beyond the standard schema:

- `vehicleRole` — `2` for the subject (instrumented) vehicle, `1` for adjacent vehicles
- `type_of_vehicle`, `length`, `width`, `height` — raw object dimensions (m)

Extra metadata columns: `corridor`, `run_number`, `sub_run_number`,
`roadway_type`, `aggressiveness`, `following_distance`, `speed_limits`,
`route_distance`, `map_origin_lon/lat/alt`, `annual_traffic_density`.

---

#### Notes on `ADAS_two_vehicle` (FHWA ADAS Two-Vehicle, Central Ohio)

Same partitioning and output layout as `ADAS_single`, but each collection carries
two subject vehicles. They appear as `carId = 0_1` and `0_2` (both
`vehicleRole=2`), alongside adjacent vehicles (`vehicleRole=1`).

```bash
python factory.py --dataset ADAS_two_vehicle --data_folder ./original_data/ADAS --save_folder ./processed_data/ADAS_two_vehicle
```

Coordinate handling, `objClass` rule, and extra trajectory columns match
`ADAS_single`. The metadata adds one further column, `gap_level`, on top of the
single-vehicle set.

---

#### Notes on `OpenACC` (JRC Car-Following Platoon)

The JRC OpenACC release is organized by **campaign** (AstaZero, Casale, Cherasco,
JRC low speed, Vicolungo, ZalaZone). The converter walks each campaign sub-folder
under `--data_folder`; every platoon CSV (a 5-row embedded header followed by
wide multi-vehicle columns) becomes one collection at
`<save_folder>/<campaign>/<YYYYMMDD>_<file_stem>/`. Per-campaign and root
`recordings_index.csv` files are written. The OBD-only
`One_vehicle_multiple_drivers_on_road_campaign` is skipped.

```bash
python factory.py --dataset OpenACC --data_folder ./original_data/OpenACC --save_folder ./processed_data/OpenACC
```

Optional keys: `campaign` (process one campaign), `test_file` (one CSV by name),
`limit` (max CSVs per campaign).

Each vehicle in a platoon is one `carId` (the index of its `SpeedN` column).
Positions come from the GNSS map frame `E`/`N` (meters) and fill
`carCenterXm` / `carCenterYm`; `carCenterLon` / `carCenterLat` come from the
source `Lon`/`Lat` columns (radians in the JRC docs, converted to degrees, with a
guard for ZalaZone files already stored in degrees). `course` is derived from the
velocity components `VE`/`VN`, falling back to successive `E`/`N` differences.
OpenACC has no detected bounding boxes, so oriented boxes are synthesized from an
assumed 4.8 m × 1.8 m footprint; pixel coordinates are `-1`. Output frame rate is
10 Hz, and all agents use `objClass=0`.

Extra trajectory column: `driver` — `Human` or `ACC`, resolved from the per-vehicle
`Driver` column or the file-level `ACC` mode.

Extra metadata columns: `vehicle_order`, `number_of_vehicles`,
`distance_setting`, `test_environment`, `equipment`.

> OpenACC records the driving mode per vehicle in the `driver` column rather than
> the shared `vehicleRole` column, so `vehicleRole` is not emitted for this dataset.

---

### objClass Reference (NBDT Standard)

Defined in the NBDT wiki. New types are appended to this table when added.

| `objClass` | Vehicle type | Datasets |
|-----------|-------------|---------|
| -1 | Undifferentiated / unknown | all (fallback) |
| 0  | Car (generic vehicle for Waymo) | highD, inD, NGSIM, Waymo, Lyft, OpenACC, ADAS_single, ADAS_two_vehicle |
| 1  | Taxi | *(reserved, no current dataset)* |
| 2  | Bus | UTE, Lyft |
| 3  | Truck | highD, inD, NGSIM, Lyft, ADAS_single, ADAS_two_vehicle |
| 4  | Motorcycle / cyclist / bicycle | NGSIM, Waymo, Lyft, inD |
| 5  | Pedestrian | inD, Waymo, Lyft |

> **ADAS note**: `objClass` is inferred from vehicle length (`> 10 m` → `3`,
> else `0`). **OpenACC note**: all platoon vehicles are passenger cars, so every
> agent is `objClass=0`.

### AV / HDV Indicator Column

`objClass` describes vehicle category only. Whether a vehicle is an AV (CAV)
or a human-driven vehicle (HDV) is recorded in the unified `vehicleRole` column,
shared by all datasets that carry this information:

| `vehicleRole` | Meaning | Datasets |
|---|---|---|
| 0 | Surrounding / non-vehicle agent (role unconfirmed or not applicable) | Lyft (all non-ego), Waymo (pedestrian / cyclist) |
| 1 | HDV — confirmed human-driven vehicle / adjacent vehicle | Waymo, ADAS_single, ADAS_two_vehicle |
| 2 | AV / ego or subject data-collection vehicle | Waymo, Lyft, ADAS_single, ADAS_two_vehicle |

> **Lyft note**: surrounding agents are not individually labelled as HDV or AV,
> so they all receive `vehicleRole=0`. Value `1` (confirmed HDV) is not
> produced by `LyftTransfer`.
>
> **Waymo note**: Waymo distinguishes ego AV (`vehicleRole=2`), other HDVs
> (`vehicleRole=1`), and non-vehicle agents such as pedestrians and cyclists
> (`vehicleRole=0`).
>
> **ADAS note**: the instrumented subject vehicles (`SV` / `SV1` / `SV2`) carry
> `vehicleRole=2`; the surrounding adjacent vehicles carry `vehicleRole=1`.
>
> **OpenACC note**: driving mode is recorded per vehicle in the `driver`
> column (`Human` / `ACC`) rather than `vehicleRole`, which is not emitted.

If a future dataset needs additional role values, append them to this table
and document them here.
