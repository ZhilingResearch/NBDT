"""FHWA ADAS single-vehicle CSV -> Ozone (NBDT) trajectory + metadata.

Partitioning: one numbered output folder per field collection, keyed by
``date``, ``time of day``, ``route starting point(rs)``, ``route ending point(re)``.

Output layout::

    <save_folder>/
        {corridor}_{YYYYMMDD}_{HHMMSS}_run{run}_sub{sub}/
            metadata.csv
            trajectory.csv
        recordings_index.csv
"""

from __future__ import annotations

import math
import os
import re
from datetime import datetime
from typing import Iterable, List, Tuple

import numpy as np
import pandas as pd

from dataloader import BasicTransfer


EARTH_RADIUS_M = 6378137.0
OUTPUT_FPS = 10.0
EGO_CAR_ID = 0
DATASET_NAME = "ADAS_SingleVehicle_Ohio"

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
    "corridor",
    "run_number",
    "sub_run_number",
    "roadway_type",
    "aggressiveness",
    "following_distance",
    "speed_limits",
    "route_distance",
    "map_origin_lon",
    "map_origin_lat",
    "map_origin_alt",
    "annual_traffic_density",
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

EXTRA_TRAJECTORY_COLUMNS = (
    "vehicleRole",
    "type_of_vehicle",
    "length",
    "width",
    "height",
)


def normalize_date(date_str: str) -> str:
    text = str(date_str).strip().replace("_", "-")
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text


def format_recording_date(date_str: str) -> str:
    return normalize_date(date_str)


def format_recording_time(time_of_day: str) -> str:
    parts = str(time_of_day).strip().split("-")
    if len(parts) >= 2:
        return f"{parts[0]}:{parts[1]}"
    return str(time_of_day)


def weekday_from_date(date_str: str) -> str:
    try:
        return datetime.strptime(normalize_date(date_str), "%Y-%m-%d").strftime("%A")
    except ValueError:
        return ""


def slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", str(text).strip())
    slug = slug.strip("_")
    return slug[:max_len] if slug else "unknown"


def site_name_from_row(row: pd.Series) -> str:
    start = slugify(row["route starting point(rs)"], 28)
    end = slugify(row["route ending point(re)"], 28)
    return f"{start}_to_{end}"


def collection_key_from_row(row: pd.Series) -> Tuple[str, str, str, str]:
    return (
        normalize_date(row["date"]),
        str(row["time of day"]).strip(),
        str(row["route starting point(rs)"]).strip(),
        str(row["route ending point(re)"]).strip(),
    )


def time_to_frame_num(time_s: np.ndarray) -> np.ndarray:
    return np.rint(time_s * OUTPUT_FPS).astype(np.int64)


def normalize_map_heading(heading_map_deg: np.ndarray) -> np.ndarray:
    return np.mod(heading_map_deg, 360.0)


def map_heading_to_course(heading_map_deg: np.ndarray) -> np.ndarray:
    h = np.radians(np.asarray(heading_map_deg, dtype=np.float64))
    return np.mod(np.degrees(np.arctan2(np.cos(h), np.sin(h))), 360.0)


def meters_to_lonlat(
    east_m: np.ndarray,
    north_m: np.ndarray,
    origin_lon: np.ndarray,
    origin_lat: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    lat0 = np.radians(origin_lat)
    dlat = np.asarray(north_m, dtype=np.float64) / EARTH_RADIUS_M
    dlon = np.asarray(east_m, dtype=np.float64) / (
        EARTH_RADIUS_M * np.cos(lat0)
    )
    lat = origin_lat + np.degrees(dlat)
    lon = origin_lon + np.degrees(dlon)
    return lon, lat


def infer_obj_class(length_m: np.ndarray) -> np.ndarray:
    return np.where(length_m > 10.0, 3, 0).astype(np.int64)


def compute_obb_corners(
    cx: np.ndarray,
    cy: np.ndarray,
    length_m: np.ndarray,
    width_m: np.ndarray,
    heading_deg: np.ndarray,
) -> Tuple[np.ndarray, ...]:
    half_l = length_m / 2.0
    half_w = width_m / 2.0
    theta = np.radians(heading_deg)
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


def build_agent_records(
    frame_num: np.ndarray,
    car_id: np.ndarray,
    east_m: np.ndarray,
    north_m: np.ndarray,
    heading_map: np.ndarray,
    speed: np.ndarray,
    length_m: np.ndarray,
    width_m: np.ndarray,
    height_m: np.ndarray,
    lane_id: np.ndarray,
    vehicle_role: int,
    type_of_vehicle: pd.Series,
    origin_lon: np.ndarray,
    origin_lat: np.ndarray,
) -> pd.DataFrame:
    heading = normalize_map_heading(heading_map)
    course = map_heading_to_course(heading_map)
    obj_class = infer_obj_class(length_m)

    bb1xm, bb1ym, bb2xm, bb2ym, bb3xm, bb3ym, bb4xm, bb4ym = compute_obb_corners(
        east_m, north_m, length_m, width_m, heading_map
    )
    lon, lat = meters_to_lonlat(east_m, north_m, origin_lon, origin_lat)
    n = len(frame_num)
    neg_one = np.full(n, -1.0)

    return pd.DataFrame(
        {
            "frameNum": frame_num,
            "carId": car_id,
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
            "carCenterXm": east_m,
            "carCenterYm": north_m,
            "boundingBox1Xm": bb1xm,
            "boundingBox1Ym": bb1ym,
            "boundingBox2Xm": bb2xm,
            "boundingBox2Ym": bb2ym,
            "boundingBox3Xm": bb3xm,
            "boundingBox3Ym": bb3ym,
            "boundingBox4Xm": bb4xm,
            "boundingBox4Ym": bb4ym,
            "heading": heading,
            "course": course,
            "speed": speed,
            "objClass": obj_class,
            "carCenterLon": lon,
            "carCenterLat": lat,
            "laneId": lane_id.astype(np.int64),
            "vehicleRole": vehicle_role,
            "type_of_vehicle": type_of_vehicle.astype(object),
            "length": length_m,
            "width": width_m,
            "height": height_m,
        }
    )


def first_non_null(series: pd.Series):
    valid = series.dropna()
    if valid.empty:
        return np.nan
    return valid.iloc[0]


class ADASOneVehicleTransfer(BasicTransfer):
    """Convert FHWA ADAS single-vehicle naturalistic CSV to Ozone format.

    Expected input: one appended CSV under ``data_folder`` (default file name
    ``Advanced_Driver_Assistance_System__ADAS_-Equipped_Single-Vehicle_Data_...``).

    Writes numbered sub-folders under ``save_folder``, each containing
    ``metadata.csv`` (one row) and ``trajectory.csv``, plus
    ``recordings_index.csv`` at the root.

    Optional ``args.test_run`` / ``args.test_sub_run`` filter rows for debugging.
    """

    DEFAULT_CSV = (
        "Advanced_Driver_Assistance_System__ADAS_-Equipped_"
        "Single-Vehicle_Data_for_Central_Ohio.csv"
    )

    USECOLS = [
        "ID",
        "Time",
        "pos_x_av_m",
        "pos_y_av_m",
        "heading_av_m",
        "dim_x_av",
        "dim_y_av",
        "dim_z_av",
        "speed_av",
        "lane_id_av",
        "pos_x_sv_m",
        "pos_y_sv_m",
        "heading_sv",
        "dim_x_sv",
        "dim_y_sv",
        "dim_z_sv",
        "speed_sv",
        "lane_id_sv",
        "map_origin_x",
        "map_origin_y",
        "map_origin_z",
        "run number",
        "sub run number",
        "date",
        "time of day",
        "route starting point(rs)",
        "route ending point(re)",
        "distance",
        "maplink",
        "roadway type",
        "speed limits",
        "road condition",
        "type of vehicle",
        "aggressiveness",
        "following distance",
        "annual traffic density",
    ]

    CHUNK_SIZE = 500_000
    MILE_TO_M = 1609.344
    MPH_TO_MPS = 0.44704

    @staticmethod
    def _is_missing(value) -> bool:
        if value is None:
            return True
        if isinstance(value, float) and math.isnan(value):
            return True
        if isinstance(value, str) and not value.strip():
            return True
        return False

    @classmethod
    def parse_route_distance_to_m(cls, value) -> float:
        if cls._is_missing(value):
            return float("nan")
        text = str(value).strip().lower()
        if text in {"-", "nan"}:
            return float("nan")
        match = re.search(r"~?\s*([\d.]+)", text)
        if not match:
            return float("nan")
        miles = float(match.group(1))
        return round(miles * cls.MILE_TO_M, 3)

    @classmethod
    def convert_speed_limits_to_mps(cls, value) -> str:
        if cls._is_missing(value):
            return ""
        text = str(value).strip()
        if not text:
            return ""

        def repl(match: re.Match[str]) -> str:
            mph = float(match.group(0))
            mps = mph * cls.MPH_TO_MPS
            formatted = f"{mps:.3f}".rstrip("0").rstrip(".")
            return formatted if formatted else "0"

        return re.sub(r"\d+\.?\d*", repl, text)

    @staticmethod
    def format_time_compact(time_of_day: str) -> str:
        return str(time_of_day).strip().replace(":", "").replace("-", "")

    @staticmethod
    def corridor_from_routes(route_start, route_end) -> str:
        start = "" if pd.isna(route_start) else str(route_start).strip().lower()
        end = "" if pd.isna(route_end) else str(route_end).strip().lower()
        text = f"{start} {end}"
        if not start and not end:
            return "UNK"
        if "summit st" in text or "used kids" in text or "evolved body" in text:
            return "US23_SUMMIT"
        if "marysville" in text or "us-42" in text or (
            "5th st" in text and "marathon" in text
        ):
            return "US33_MSV"
        if "perimeter loop" in text or "3760 main" in text or (
            "hilliard" in text and "panera" in text
        ):
            return "US33_HIL"
        if "1090 dublin" in text or (
            "wendy" in text and "bp" in text and "dublin granville" in text
        ):
            return "US315"
        if "dublin granville" in text or "1093 dublin" in text or (
            "starbucks" in text and "dublin" in text
        ):
            return "US33_DUB"
        if "lewis center" in text or "maxtown" in text or "8870 columbus pike" in text:
            return "I670"
        if "delaware" in text or "waldo" in text or "radnor" in text or (
            "huntington bank" in text and "columbus pike" in text
        ):
            return "US23"
        if "i-270" in text:
            return "I270"
        if "worthington" in text or "olentangy" in text or "i-71" in text:
            return "I71_OLE"
        if (
            "morse rd" in text
            or "n broadway" in text
            or "easton gateway" in text
            or "shepard branch" in text
            or "northgate" in text
            or "new bond" in text
            or "maize-morse" in text
        ):
            return "I270"
        return "OTHER"

    @classmethod
    def collection_folder_name(
        cls,
        date: str,
        time_of_day: str,
        route_start: str,
        route_end: str,
        run_number: int,
        sub_run_number: int,
    ) -> str:
        corridor = cls.corridor_from_routes(route_start, route_end)
        ymd = normalize_date(date).replace("-", "")
        hhmmss = cls.format_time_compact(time_of_day)
        return f"{corridor}_{ymd}_{hhmmss}_run{run_number:02d}_sub{sub_run_number}"

    @classmethod
    def allocate_recording_id(
        cls,
        date: str,
        time_of_day: str,
        route_start: str,
        route_end: str,
        run_number: int,
        sub_run_number: int,
        used_ids: set[str],
    ) -> str:
        base = cls.collection_folder_name(
            date, time_of_day, route_start, route_end, run_number, sub_run_number
        )
        recording_id = base
        suffix = 2
        while recording_id in used_ids:
            recording_id = f"{base}_{suffix:02d}"
            suffix += 1
        used_ids.add(recording_id)
        return recording_id

    @staticmethod
    def build_metadata_row(segment: pd.DataFrame) -> dict:
        sample = segment.sort_values("Time").iloc[0]
        duration = float(segment["Time"].max() - segment["Time"].min())
        frame_nums = time_to_frame_num(segment["Time"].unique())
        total_frames = int(frame_nums.max()) + 1 if len(frame_nums) else 0

        maplink = first_non_null(segment.get("maplink", pd.Series([np.nan])))
        map_value = str(maplink) if pd.notna(maplink) else "-"

        ozone = {
            "datasetName": DATASET_NAME,
            "siteName": site_name_from_row(sample),
            "recordingDate": format_recording_date(sample["date"]),
            "weekDay": weekday_from_date(sample["date"]),
            "localWeather": str(first_non_null(segment["road condition"])),
            "recordingTime": format_recording_time(sample["time of day"]),
            "recordingFrameRate": int(OUTPUT_FPS),
            "totalFrames": total_frames,
            "duration": round(duration, 3),
            "map": map_value,
            "laneRange": "-",
        }

        extras = {
            "corridor": ADASOneVehicleTransfer.corridor_from_routes(
                sample["route starting point(rs)"], sample["route ending point(re)"]
            ),
            "run_number": int(first_non_null(segment["run number"])),
            "sub_run_number": int(first_non_null(segment["sub run number"])),
            "roadway_type": str(first_non_null(segment["roadway type"])),
            "aggressiveness": first_non_null(segment["aggressiveness"]),
            "following_distance": first_non_null(segment["following distance"]),
            "speed_limits": ADASOneVehicleTransfer.convert_speed_limits_to_mps(
                first_non_null(segment["speed limits"])
            ),
            "route_distance": ADASOneVehicleTransfer.parse_route_distance_to_m(
                first_non_null(segment["distance"])
            ),
            "map_origin_lon": float(sample["map_origin_x"]),
            "map_origin_lat": float(sample["map_origin_y"]),
            "map_origin_alt": float(first_non_null(segment["map_origin_z"])),
            "annual_traffic_density": str(
                first_non_null(segment["annual traffic density"])
            ),
        }

        return {**ozone, **extras}

    def __init__(self, args):
        super().__init__(args)
        self.test_run = getattr(args, "test_run", None)
        self.test_sub_run = getattr(args, "test_sub_run", None)

    def get_csv_path(self) -> str:
        folder = self.args.data_folder
        explicit = getattr(self.args, "csv_path", None)
        if explicit:
            return explicit
        default = os.path.join(folder, self.DEFAULT_CSV)
        if os.path.isfile(default):
            return default
        rows_csv = os.path.join(folder, "rows.csv")
        if os.path.isfile(rows_csv):
            return rows_csv
        for name in os.listdir(folder):
            if name.endswith(".csv") and "Single-Vehicle" in name:
                return os.path.join(folder, name)
        raise FileNotFoundError(f"No ADAS single-vehicle CSV found under {folder}")

    def _iter_filtered_chunks(self) -> Iterable[pd.DataFrame]:
        csv_path = self.get_csv_path()
        for chunk in pd.read_csv(
            csv_path,
            usecols=self.USECOLS,
            chunksize=self.CHUNK_SIZE,
            low_memory=False,
        ):
            chunk = chunk[chunk["run number"].notna()].copy()
            if self.test_run is not None:
                chunk = chunk[chunk["run number"] == float(self.test_run)]
            if self.test_sub_run is not None:
                chunk = chunk[chunk["sub run number"] == float(self.test_sub_run)]
            if chunk.empty:
                continue
            chunk["run number"] = chunk["run number"].astype(int)
            chunk["sub run number"] = chunk["sub run number"].astype(int)
            chunk["collectionKey"] = chunk.apply(collection_key_from_row, axis=1)
            yield chunk

    def _process_segment(self, segment: pd.DataFrame) -> pd.DataFrame:
        """Build trajectories with one SV row per Time and one AdjV row per (Time, ID).

        Raw rows are keyed by adjacent-vehicle ``ID``; the same ``Time`` can appear
        on many rows (multiple AdjV at one instant, or overlapping encounter
        segments). Emitting one SV record per raw row duplicates ``(frameNum,
        carId=0)`` and can assign conflicting SV states at the same frame.
        """
        segment = segment.sort_values(["Time", "ID"]).reset_index(drop=True)
        sv_source = segment.drop_duplicates(subset=["Time"], keep="first")
        av_source = segment.drop_duplicates(subset=["Time", "ID"], keep="first")

        origin_lon = segment["map_origin_x"].values.astype(np.float64)
        origin_lat = segment["map_origin_y"].values.astype(np.float64)
        type_of_vehicle = segment["type of vehicle"].fillna("")

        sv = build_agent_records(
            frame_num=time_to_frame_num(sv_source["Time"].values),
            car_id=np.full(len(sv_source), EGO_CAR_ID, dtype=np.int64),
            east_m=sv_source["pos_x_sv_m"].values,
            north_m=sv_source["pos_y_sv_m"].values,
            heading_map=sv_source["heading_sv"].values,
            speed=sv_source["speed_sv"].values,
            length_m=sv_source["dim_x_sv"].values,
            width_m=sv_source["dim_y_sv"].values,
            height_m=sv_source["dim_z_sv"].values,
            lane_id=sv_source["lane_id_sv"].values,
            vehicle_role=2,
            type_of_vehicle=type_of_vehicle.loc[sv_source.index],
            origin_lon=sv_source["map_origin_x"].values.astype(np.float64),
            origin_lat=sv_source["map_origin_y"].values.astype(np.float64),
        )

        av = build_agent_records(
            frame_num=time_to_frame_num(av_source["Time"].values),
            car_id=av_source["ID"].astype(np.int64).values,
            east_m=av_source["pos_x_av_m"].values,
            north_m=av_source["pos_y_av_m"].values,
            heading_map=av_source["heading_av_m"].values,
            speed=av_source["speed_av"].values,
            length_m=av_source["dim_x_av"].values,
            width_m=av_source["dim_y_av"].values,
            height_m=av_source["dim_z_av"].values,
            lane_id=av_source["lane_id_av"].values,
            vehicle_role=1,
            type_of_vehicle=type_of_vehicle.loc[av_source.index],
            origin_lon=av_source["map_origin_x"].values.astype(np.float64),
            origin_lat=av_source["map_origin_y"].values.astype(np.float64),
        )

        combined = pd.concat([sv, av], ignore_index=True)
        combined = combined.sort_values(["frameNum", "carId"]).drop_duplicates(
            subset=["frameNum", "carId"], keep="first"
        )
        return combined[[*STANDARD_COLUMNS, *EXTRA_TRAJECTORY_COLUMNS]]

    def _process_data(self, file_path: str) -> pd.DataFrame:
        raise NotImplementedError(
            "ADASOneVehicleTransfer writes numbered folders; use run() instead."
        )

    @staticmethod
    def _sort_collection_keys(
        keys: Iterable[Tuple[str, str, str, str]],
    ) -> List[Tuple[str, str, str, str]]:
        return sorted(keys, key=lambda k: (k[0], k[1], k[2], k[3]))

    def run(self) -> None:
        os.makedirs(self.args.save_folder, exist_ok=True)

        segments: dict[Tuple[str, str, str, str], List[pd.DataFrame]] = {}
        csv_path = self.get_csv_path()
        for chunk in self._iter_filtered_chunks():
            for key, part in chunk.groupby("collectionKey", sort=False):
                segments.setdefault(key, []).append(part)

        if not segments:
            raise RuntimeError("No rows matched the current filters.")

        collection_keys = self._sort_collection_keys(segments.keys())
        index_rows = []
        used_recording_ids: set[str] = set()

        for key in collection_keys:
            segment = pd.concat(segments[key], ignore_index=True)
            date, tod, route_start, route_end = key
            run_number = int(first_non_null(segment["run number"]))
            sub_run_number = int(first_non_null(segment["sub run number"]))
            recording_id = self.allocate_recording_id(
                date,
                tod,
                route_start,
                route_end,
                run_number,
                sub_run_number,
                used_recording_ids,
            )
            out_dir = os.path.join(self.args.save_folder, recording_id)
            os.makedirs(out_dir, exist_ok=True)

            processed = self._process_segment(segment)

            meta_path = os.path.join(out_dir, "metadata.csv")
            traj_path = os.path.join(out_dir, "trajectory.csv")

            pd.DataFrame([self.build_metadata_row(segment)])[list(METADATA_COLUMNS)].to_csv(
                meta_path, index=False
            )
            processed.to_csv(traj_path, index=False)

            date, tod, route_start, route_end = key
            index_rows.append(
                {
                    "recordingIndex": recording_id,
                    "corridor": self.corridor_from_routes(route_start, route_end),
                    "date": date,
                    "time_of_day": tod,
                    "route_start": route_start,
                    "route_end": route_end,
                    "metadata_file": os.path.join(recording_id, "metadata.csv"),
                    "trajectory_file": os.path.join(recording_id, "trajectory.csv"),
                    "source_rows": len(segment),
                    "trajectory_rows": len(processed),
                }
            )
            print("  Processed →", out_dir)

        index_path = os.path.join(self.args.save_folder, "recordings_index.csv")
        pd.DataFrame(index_rows).to_csv(index_path, index=False)
        print(f"  ADAS one-vehicle: {csv_path} → {len(collection_keys)} collections")
        print("  Processed →", index_path)
