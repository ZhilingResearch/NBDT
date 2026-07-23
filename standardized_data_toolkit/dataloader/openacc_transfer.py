"""JRC OpenACC platoon CSV -> Ozone (NBDT) trajectory + metadata.

Each platoon CSV (5-row embedded header + wide multi-vehicle columns) becomes
one collection under ``<save_folder>/<campaign>/<YYYYMMDD>_<stem>/``.

Skips ``One_vehicle_multiple_drivers_on_road_campaign`` (OBD-only, no GNSS).

Output layout::

    <save_folder>/
        AstaZero/
            {YYYYMMDD}_{file_stem}/
                metadata.csv
                trajectory.csv
            recordings_index.csv
        ...
        recordings_index.csv
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd

from dataloader import BasicTransfer

OUTPUT_FPS = 10.0
DATASET_NAME = "OpenACC"
NEG_ONE = -1.0
DEFAULT_OBJ_CLASS = 0
VEHICLE_LENGTH_M = 4.8
VEHICLE_WIDTH_M = 1.8

SKIP_CAMPAIGN = "One_vehicle_multiple_drivers_on_road_campaign"
SKIP_CSV_SUBSTRINGS = ("specification", "long setting")

PLATOON_CAMPAIGNS: Tuple[str, ...] = (
    "AstaZero",
    "Casale",
    "Cherasco",
    "JRC low speed",
    "Vicolungo",
    "ZalaZone",
)

OZONE_METADATA_COLUMNS = (
    "datasetName",
    "siteName",
    "recordingDate",
    "weekDay",
    "localWeather",
    "recordingTime",
    "recordingFrameRate",
    "totalFrames",
    "duration",
    "map",
    "laneRange",
)

EXTRA_METADATA_COLUMNS = (
    "vehicle_order",
    "number_of_vehicles",
    "distance_setting",
    "test_environment",
    "equipment",
)

METADATA_COLUMNS = OZONE_METADATA_COLUMNS + EXTRA_METADATA_COLUMNS

STANDARD_COLUMNS = (
    "frameNum",
    "carId",
    "carCenterX",
    "carCenterY",
    "boundingBox1X",
    "boundingBox1Y",
    "boundingBox2X",
    "boundingBox2Y",
    "boundingBox3X",
    "boundingBox3Y",
    "boundingBox4X",
    "boundingBox4Y",
    "carCenterXm",
    "carCenterYm",
    "boundingBox1Xm",
    "boundingBox1Ym",
    "boundingBox2Xm",
    "boundingBox2Ym",
    "boundingBox3Xm",
    "boundingBox3Ym",
    "boundingBox4Xm",
    "boundingBox4Ym",
    "heading",
    "course",
    "speed",
    "objClass",
    "carCenterLon",
    "carCenterLat",
    "laneId",
)

EXTRA_TRAJECTORY_COLUMNS = ("driver",)

CAMPAIGN_CONFIG: Dict[str, Dict[str, str]] = {
    "AstaZero": {
        "site_name": "AstaZero Rural Road",
        "test_environment": "proving_ground",
        "map": "AstaZero test track, Rural road (~5.7 km), Sweden",
        "equipment": "OxTS RT-Range S",
    },
    "Casale": {
        "site_name": "Ispra-Casale Monferrato Highway",
        "test_environment": "public_highway",
        "map": "Public roads, Ispra to Casale Monferrato, Italy",
        "equipment": "Ublox 9, OBD",
    },
    "Cherasco": {
        "site_name": "Ispra-Cherasco Highway",
        "test_environment": "public_highway",
        "map": "Public freeway, Ispra (VA) to Cherasco (CO), Italy",
        "equipment": "Ublox 8, OBD",
    },
    "JRC low speed": {
        "site_name": "JRC Ispra Campus",
        "test_environment": "campus",
        "map": "JRC Ispra territory, Italy",
        "equipment": "Ublox 9, OBD",
    },
    "Vicolungo": {
        "site_name": "Ispra-Vicolungo Highway",
        "test_environment": "public_highway",
        "map": "Public roads, Ispra (VA) to Vicolungo (NO), Italy",
        "equipment": "Ublox 8, OBD",
    },
    "ZalaZone": {
        "site_name": "ZalaZONE Proving Ground",
        "test_environment": "proving_ground",
        "map": "ZalaZONE Dynamic Platform / Handling Course, Hungary",
        "equipment": "INVENTURE VBOX, Ublox 9, Tracker App",
    },
}


def weekday_from_date(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
    except ValueError:
        return ""


def parse_embedded_date(parts: Sequence[str]) -> str:
    """Parse ``Date,DD,MM,YYYY`` row tail into ``YYYY-MM-DD``."""
    nums = [p.strip() for p in parts if p.strip()]
    if len(nums) >= 3:
        dd, mm, yyyy = nums[0], nums[1], nums[2]
        try:
            return datetime(int(yyyy), int(mm), int(dd)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""


def parse_header_rows(header_lines: Sequence[str]) -> dict:
    meta: dict = {}
    for line in header_lines:
        parts = line.rstrip("\n").split(",")
        key = parts[0].strip()
        values = [p.strip() for p in parts[1:] if p.strip()]
        meta[key] = values
    recording_date = parse_embedded_date(meta.get("Date", []))
    vehicle_order = meta.get("Vehicle_order", [])
    acc_raw = meta.get("ACC", [""])
    acc_mode = acc_raw[0].strip() if acc_raw else ""
    dist_raw = meta.get("Distance_setting", [""])
    distance_setting = dist_raw[0].strip() if dist_raw else ""
    return {
        "recording_date": recording_date,
        "vehicle_order": vehicle_order,
        "acc_mode": acc_mode if acc_mode else "unknown",
        "distance_setting": distance_setting if distance_setting else "-",
    }


def is_platoon_csv(csv_path: Path) -> bool:
    with csv_path.open(encoding="utf-8", errors="replace") as handle:
        first = handle.readline()
    return not first.startswith("Time,Speed,Engine")


def should_skip_csv(csv_path: Path) -> bool:
    name_lower = csv_path.name.lower()
    return any(token in name_lower for token in SKIP_CSV_SUBSTRINGS)


def discover_vehicle_indices(columns: Sequence[str]) -> List[int]:
    indices: List[int] = []
    for col in columns:
        match = re.fullmatch(r"Speed(\d+)", col)
        if match:
            indices.append(int(match.group(1)))
    return sorted(set(indices))


def time_to_frame_num(time_s: np.ndarray) -> np.ndarray:
    return np.rint(time_s * OUTPUT_FPS).astype(np.int64)


def compute_course_from_en(east: np.ndarray, north: np.ndarray) -> np.ndarray:
    """Heading relative to global North (Ozone ``course``), degrees [0, 360)."""
    east = np.asarray(east, dtype=np.float64)
    north = np.asarray(north, dtype=np.float64)
    de = np.diff(east, prepend=east[0])
    dn = np.diff(north, prepend=north[0])
    if len(east) > 1:
        de[0] = east[1] - east[0]
        dn[0] = north[1] - north[0]
    course = np.full(len(east), np.nan, dtype=np.float64)
    valid = np.isfinite(de) & np.isfinite(dn)
    stationary = valid & (np.abs(de) < 1e-9) & (np.abs(dn) < 1e-9)
    moving = valid & ~stationary
    course[stationary] = 0.0
    course[moving] = np.degrees(np.arctan2(de[moving], dn[moving])) % 360.0
    return course


def compute_course_from_ve_vn(ve: np.ndarray, vn: np.ndarray) -> np.ndarray:
    """Heading relative to global North (Ozone ``course``), degrees [0, 360)."""
    ve = np.asarray(ve, dtype=np.float64)
    vn = np.asarray(vn, dtype=np.float64)
    course = np.full(len(ve), np.nan, dtype=np.float64)
    valid = np.isfinite(ve) & np.isfinite(vn)
    stationary = valid & (np.abs(ve) < 1e-9) & (np.abs(vn) < 1e-9)
    moving = valid & ~stationary
    course[stationary] = 0.0
    course[moving] = np.degrees(np.arctan2(ve[moving], vn[moving])) % 360.0
    return course


def _source_latlon_already_degrees(lat_raw: np.ndarray) -> bool:
    """Heuristic: OpenACC docs use radians; some ZalaZone files store degrees."""
    finite = lat_raw[np.isfinite(lat_raw)]
    if finite.size == 0:
        return False
    # European lat in rad is < ~1.2; in degrees is ~45–58. Threshold avoids
    # misclassifying lon values above pi/2 rad when lat is still in radians.
    return float(np.nanmax(np.abs(finite))) > 2.0


def latlon_to_deg_columns(
    data: pd.DataFrame, vehicle_idx: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Ozone ``carCenterLon`` / ``carCenterLat``: WGS84 degrees.

    Source columns ``Lon{i}`` / ``Lat{i}`` (OpenACC docs: radians) are converted
    to global longitude/latitude in degrees. They refer to the same GNSS reference
    point as ``E{i}``/``N{i}``, used as the oriented bounding-box center in map
    frame. Missing columns, NaN, or out-of-range values -> -1.
    """
    n = len(data)
    lon_col = f"Lon{vehicle_idx}"
    lat_col = f"Lat{vehicle_idx}"
    if lon_col not in data.columns or lat_col not in data.columns:
        return np.full(n, NEG_ONE), np.full(n, NEG_ONE)

    lon_raw = pd.to_numeric(data[lon_col], errors="coerce").values.astype(np.float64)
    lat_raw = pd.to_numeric(data[lat_col], errors="coerce").values.astype(np.float64)

    if _source_latlon_already_degrees(lat_raw):
        lon_deg = lon_raw.copy()
        lat_deg = lat_raw.copy()
    else:
        lon_deg = np.degrees(lon_raw)
        lat_deg = np.degrees(lat_raw)

    missing = ~np.isfinite(lon_raw) | ~np.isfinite(lat_raw)
    invalid = (
        (lat_deg < -90.0)
        | (lat_deg > 90.0)
        | (lon_deg < -180.0)
        | (lon_deg > 180.0)
    )
    lon_deg[missing | invalid] = NEG_ONE
    lat_deg[missing | invalid] = NEG_ONE
    return lon_deg, lat_deg


def compute_obb_corners(
    cx: np.ndarray,
    cy: np.ndarray,
    length_m: np.ndarray,
    width_m: np.ndarray,
    course_deg: np.ndarray,
) -> Tuple[np.ndarray, ...]:
    half_l = length_m / 2.0
    half_w = width_m / 2.0
    theta = np.radians(course_deg)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    lc = half_l * cos_t
    ls = half_l * sin_t
    wc = half_w * cos_t
    ws = half_w * sin_t
    bb1x = cx + lc + ws
    bb1y = cy + ls - wc
    bb2x = cx + lc - ws
    bb2y = cy + ls + wc
    bb3x = cx - lc - ws
    bb3y = cy - ls + wc
    bb4x = cx - lc + ws
    bb4y = cy - ls - wc
    return bb1x, bb1y, bb2x, bb2y, bb3x, bb3y, bb4x, bb4y


def resolve_driver(cell, acc_mode: str) -> str:
    if pd.notna(cell):
        text = str(cell).strip()
        if text in {"Human", "ACC"}:
            return text
    mode = str(acc_mode).strip()
    if mode == "0":
        return "Human"
    if mode == "1":
        return "ACC"
    return "unknown"


def collection_folder_name(recording_date: str, stem: str) -> str:
    ymd = recording_date.replace("-", "") if recording_date else "unknown"
    return f"{ymd}_{stem}"


def read_platoon_csv(csv_path: Path) -> Tuple[dict, pd.DataFrame]:
    with csv_path.open(encoding="utf-8", errors="replace") as handle:
        header_lines = [handle.readline() for _ in range(5)]
    header = parse_header_rows(header_lines)
    data = pd.read_csv(csv_path, skiprows=5, low_memory=False)
    return header, data


def build_vehicle_trajectory(
    data: pd.DataFrame,
    vehicle_idx: int,
    acc_mode: str,
) -> pd.DataFrame:
    time_raw = pd.to_numeric(data["Time"], errors="coerce").values
    valid_time = np.isfinite(time_raw)
    if not valid_time.any():
        return pd.DataFrame()

    t0 = float(np.nanmin(time_raw))
    time_rel = time_raw - t0
    frame_num = time_to_frame_num(time_rel)

    speed = pd.to_numeric(data.get(f"Speed{vehicle_idx}"), errors="coerce").values
    east = pd.to_numeric(data.get(f"E{vehicle_idx}"), errors="coerce").values
    north = pd.to_numeric(data.get(f"N{vehicle_idx}"), errors="coerce").values

    has_position = np.isfinite(east) & np.isfinite(north)
    if not (has_position & np.isfinite(speed)).any():
        return pd.DataFrame()

    lon_deg, lat_deg = latlon_to_deg_columns(data, vehicle_idx)

    ve_col = f"VE{vehicle_idx}"
    vn_col = f"VN{vehicle_idx}"
    if ve_col in data.columns and vn_col in data.columns:
        ve = pd.to_numeric(data[ve_col], errors="coerce").values
        vn = pd.to_numeric(data[vn_col], errors="coerce").values
        course = compute_course_from_ve_vn(ve, vn)
        bad = ~np.isfinite(ve) | ~np.isfinite(vn)
        if bad.any():
            course[bad] = compute_course_from_en(east, north)[bad]
    else:
        course = compute_course_from_en(east, north)

    driver_col = f"Driver{vehicle_idx}"
    if driver_col in data.columns:
        driver = np.array(
            [resolve_driver(value, acc_mode) for value in data[driver_col].values],
            dtype=object,
        )
    else:
        driver = np.full(len(data), resolve_driver(np.nan, acc_mode), dtype=object)

    n = len(data)
    neg_one = np.full(n, NEG_ONE)
    center_xm = np.where(has_position, east, np.nan)
    center_ym = np.where(has_position, north, np.nan)
    length_m = np.full(n, VEHICLE_LENGTH_M, dtype=np.float64)
    width_m = np.full(n, VEHICLE_WIDTH_M, dtype=np.float64)
    course_for_bbox = np.where(np.isfinite(course), course, 0.0)
    bb1xm, bb1ym, bb2xm, bb2ym, bb3xm, bb3ym, bb4xm, bb4ym = compute_obb_corners(
        center_xm, center_ym, length_m, width_m, course_for_bbox
    )

    return pd.DataFrame(
        {
            "frameNum": frame_num,
            "carId": np.full(n, vehicle_idx, dtype=np.int64),
            "carCenterX": neg_one,
            "carCenterY": neg_one,
            "boundingBox1X": neg_one,
            "boundingBox1Y": neg_one,
            "boundingBox2X": neg_one,
            "boundingBox2Y": neg_one,
            "boundingBox3X": neg_one,
            "boundingBox3Y": neg_one,
            "boundingBox4X": neg_one,
            "boundingBox4Y": neg_one,
            "carCenterXm": center_xm,
            "carCenterYm": center_ym,
            "boundingBox1Xm": bb1xm,
            "boundingBox1Ym": bb1ym,
            "boundingBox2Xm": bb2xm,
            "boundingBox2Ym": bb2ym,
            "boundingBox3Xm": bb3xm,
            "boundingBox3Ym": bb3ym,
            "boundingBox4Xm": bb4xm,
            "boundingBox4Ym": bb4ym,
            "heading": neg_one,
            "course": course,
            "speed": speed,
            "objClass": np.full(n, DEFAULT_OBJ_CLASS, dtype=np.int64),
            "carCenterLon": lon_deg,
            "carCenterLat": lat_deg,
            "laneId": np.full(n, -1, dtype=np.int64),
            "driver": driver,
            "_valid": has_position & np.isfinite(speed) & np.isfinite(time_raw),
        }
    )


def build_metadata_row(
    campaign: str,
    header: dict,
    vehicle_indices: List[int],
    duration: float,
    total_frames: int,
) -> dict:
    """Build one metadata row for a platoon collection.

    ``number_of_vehicles``: count of ``SpeedN`` columns in the data block
    (vehicles with trajectory data in this file).
    """
    cfg = CAMPAIGN_CONFIG.get(campaign, {})
    recording_date = header["recording_date"] or "-"
    vehicle_order = ",".join(header["vehicle_order"]) if header["vehicle_order"] else "-"

    ozone = {
        "datasetName": DATASET_NAME,
        "siteName": cfg.get("site_name", campaign),
        "recordingDate": recording_date,
        "weekDay": weekday_from_date(recording_date) if recording_date != "-" else "",
        "localWeather": "-",
        "recordingTime": "-",
        "recordingFrameRate": int(OUTPUT_FPS),
        "totalFrames": total_frames,
        "duration": round(duration, 3),
        "map": cfg.get("map", "-"),
        "laneRange": "-",
    }
    extras = {
        "vehicle_order": vehicle_order,
        "number_of_vehicles": len(vehicle_indices),
        "distance_setting": header["distance_setting"],
        "test_environment": cfg.get("test_environment", "-"),
        "equipment": cfg.get("equipment", "-"),
    }
    return {**ozone, **extras}


def process_platoon_csv(
    csv_path: Path,
    campaign: str,
) -> Tuple[dict, pd.DataFrame]:
    header, data = read_platoon_csv(csv_path)
    vehicle_indices = discover_vehicle_indices(data.columns.tolist())
    if not vehicle_indices:
        raise ValueError(f"No SpeedN columns found in {csv_path}")

    parts: List[pd.DataFrame] = []
    for idx in vehicle_indices:
        part = build_vehicle_trajectory(
            data,
            idx,
            header["acc_mode"],
        )
        if not part.empty:
            parts.append(part)

    if not parts:
        raise ValueError(f"No valid trajectory rows in {csv_path}")

    combined = pd.concat(parts, ignore_index=True)
    combined = combined[combined["_valid"]].drop(columns=["_valid"])
    combined = combined.sort_values(["frameNum", "carId"]).drop_duplicates(
        subset=["frameNum", "carId"], keep="first"
    )

    time_raw = pd.to_numeric(data["Time"], errors="coerce")
    duration = float(time_raw.max() - time_raw.min())
    total_frames = int(combined["frameNum"].max()) + 1 if not combined.empty else 0

    metadata = build_metadata_row(
        campaign=campaign,
        header=header,
        vehicle_indices=vehicle_indices,
        duration=duration,
        total_frames=total_frames,
    )
    return metadata, combined[[*STANDARD_COLUMNS, *EXTRA_TRAJECTORY_COLUMNS]]


class OpenACCTransfer(BasicTransfer):
    """Convert JRC OpenACC platoon CSV files to Ozone format."""

    def __init__(self, args):
        super().__init__(args)
        self.data_root = Path(getattr(args, "data_folder", Path(__file__).resolve().parent / "OpenACC_data"))
        self.save_root = Path(args.save_folder)
        self.campaign_filter = getattr(args, "campaign", None)
        self.test_file = getattr(args, "test_file", None)
        self.limit = getattr(args, "limit", None)

    def iter_platoon_csvs(self) -> Iterable[Tuple[str, Path]]:
        for campaign in PLATOON_CAMPAIGNS:
            if self.campaign_filter and campaign != self.campaign_filter:
                continue
            campaign_dir = self.data_root / campaign
            if not campaign_dir.is_dir():
                continue
            csv_paths = sorted(
                p
                for p in campaign_dir.glob("*.csv")
                if is_platoon_csv(p) and not should_skip_csv(p)
            )
            if self.test_file:
                csv_paths = [p for p in csv_paths if p.name == self.test_file]
            if self.limit is not None:
                csv_paths = csv_paths[: int(self.limit)]
            for csv_path in csv_paths:
                yield campaign, csv_path

    def run(self) -> None:
        os.makedirs(self.save_root, exist_ok=True)
        all_index_rows: List[dict] = []

        for campaign in PLATOON_CAMPAIGNS:
            if self.campaign_filter and campaign != self.campaign_filter:
                continue

            campaign_rows: List[dict] = []
            used_ids: set[str] = set()
            campaign_save = self.save_root / campaign
            os.makedirs(campaign_save, exist_ok=True)

            csv_list = list(
                (c, p) for c, p in self.iter_platoon_csvs() if c == campaign
            )
            if not csv_list:
                continue

            for _, csv_path in csv_list:
                metadata, trajectory = process_platoon_csv(
                    csv_path,
                    campaign,
                )
                stem = csv_path.stem
                recording_date = metadata["recordingDate"]
                folder_name = collection_folder_name(
                    recording_date if recording_date != "-" else "unknown",
                    stem,
                )
                recording_id = folder_name
                suffix = 2
                while recording_id in used_ids:
                    recording_id = f"{folder_name}_{suffix:02d}"
                    suffix += 1
                used_ids.add(recording_id)

                out_dir = campaign_save / recording_id
                os.makedirs(out_dir, exist_ok=True)

                pd.DataFrame([metadata])[list(METADATA_COLUMNS)].to_csv(
                    out_dir / "metadata.csv", index=False
                )
                trajectory.to_csv(out_dir / "trajectory.csv", index=False)

                rel_dir = f"{campaign}/{recording_id}"
                row = {
                    "recordingIndex": recording_id,
                    "campaign": campaign,
                    "source_file": csv_path.name,
                    "recordingDate": metadata["recordingDate"],
                    "metadata_file": f"{rel_dir}/metadata.csv",
                    "trajectory_file": f"{rel_dir}/trajectory.csv",
                    "trajectory_rows": len(trajectory),
                }
                campaign_rows.append(row)
                all_index_rows.append(row)
                print("  Processed →", out_dir)

            if campaign_rows:
                index_path = campaign_save / "recordings_index.csv"
                pd.DataFrame(campaign_rows).to_csv(index_path, index=False)
                print(f"  OpenACC {campaign}: {len(campaign_rows)} collections → {index_path}")

        if all_index_rows:
            root_index = self.save_root / "recordings_index.csv"
            pd.DataFrame(all_index_rows).to_csv(root_index, index=False)
            print(f"  OpenACC total: {len(all_index_rows)} collections → {root_index}")
        elif self.campaign_filter or self.test_file:
            raise RuntimeError("No platoon CSV files matched the current filters.")
        else:
            raise RuntimeError("No platoon CSV files found under OpenACC_data.")
