import os
import numpy as np
import pandas as pd
from PIL import Image

class BasicTransfer:
    def __init__(self, args):
        self.args = args

    def get_all_data(self) -> list:
        file_names = os.listdir(self.args.data_folder)
        data_list = []
        for file_name in file_names:
            data_list.append(os.path.join(self.args.data_folder, file_name))
        return data_list

    def _process_data(self, file_path: str) -> pd.DataFrame:
        raise NotImplementedError

    def _save_data(self, processed_data: pd.DataFrame, file_name: str) -> None:
        file_name = os.path.basename(file_name)
        file_name = file_name.split(".")[0]
        save_path = os.path.join(self.args.save_folder, file_name+".csv")
        processed_data.to_csv(save_path, index=False)

    def run(self) -> None:
        data_list = self.get_all_data()
        for file_path in data_list:
            processed_data = self._process_data(file_path)
            self._save_data(processed_data, file_path)


class HighDTransfer(BasicTransfer):

    def __init__(self, args):
        super(HighDTransfer, self).__init__(args)

    def get_all_data(self) -> list:
        """Override: only return XX_tracks.csv files (skip meta/jpg files)."""
        file_names = os.listdir(self.args.data_folder)
        data_list = []
        for file_name in file_names:
            if file_name.endswith('_tracks.csv'):
                data_list.append(os.path.join(self.args.data_folder, file_name))
        data_list.sort()
        return data_list

    def _process_data(self, file_path: str) -> pd.DataFrame:
        # 对于不同的数据集transfer，补充这个函数即可。返回处理好的dataframe
        # 一般情况保持 basictransfer 不动

        # Read data files
        tracks = pd.read_csv(file_path)

        # Derive corresponding meta file paths from XX_tracks.csv
        prefix = file_path.replace('_tracks.csv', '')
        tracks_meta = pd.read_csv(prefix + '_tracksMeta.csv')

        # Merge class & drivingDirection from tracksMeta
        tracks = tracks.merge(
            tracks_meta[['id', 'class', 'drivingDirection']],
            on='id', how='left'
        )

        # Compute vehicle center coordinates (meters)
        carCenterXm = tracks['x'] + tracks['width'] / 2
        carCenterYm = tracks['y'] + tracks['height'] / 2

        # Compute speed (m/s)
        speed = np.sqrt(tracks['xVelocity']**2 + tracks['yVelocity']**2)

        # Compute heading angle (relative to image X-axis, 0-360 degrees)
        heading = np.degrees(
            np.arctan2(tracks['yVelocity'], tracks['xVelocity'])
        ) % 360

        # Handle stationary vehicles (speed=0): assign heading by drivingDirection
        #   drivingDirection=1 (upper lanes, moving left) -> 180 degrees
        #   drivingDirection=2 (lower lanes, moving right) -> 0 degrees
        stationary = (tracks['xVelocity'] == 0) & (tracks['yVelocity'] == 0)
        heading[stationary & (tracks['drivingDirection'] == 1)] = 180.0
        heading[stationary & (tracks['drivingDirection'] == 2)] = 0.0

        # Compute Oriented Bounding Box 4 corner points
        # highD: width = vehicle length, height = vehicle width
        l = tracks['width'] / 2   # half-length (along heading direction)
        w = tracks['height'] / 2  # half-width  (perpendicular to heading)
        theta = np.radians(heading)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)
        lc = l * cos_t
        ls = l * sin_t
        wc = w * cos_t
        ws = w * sin_t
        #   Corner1(front-left)   Corner2(front-right)
        #   Corner4(rear-left)    Corner3(rear-right)
        bb1Xm = carCenterXm + lc + ws
        bb1Ym = carCenterYm + ls - wc
        bb2Xm = carCenterXm + lc - ws
        bb2Ym = carCenterYm + ls + wc
        bb3Xm = carCenterXm - lc - ws
        bb3Ym = carCenterYm - ls + wc
        bb4Xm = carCenterXm - lc + ws
        bb4Ym = carCenterYm - ls - wc

        # Map vehicle class
        # highD: "Car" / "Truck" -> NBDT: 0=car, 3=truck
        class_map = {'Car': 0, 'Truck': 3}
        objClass = tracks['class'].map(class_map).fillna(-1).astype(int)

        # Convert meter coordinates to pixel coordinates on the highway background image
        # Per-recording pix2meter: road_length (m) / image_width (px)
        #   road_length = max(frontSightDistance + backSightDistance) across all vehicles
        #   image_width = XX_highway.png pixel width
        highway_img = Image.open(prefix + '_highway.png')
        img_width = highway_img.size[0]
        highway_img.close()
        road_length = (tracks['frontSightDistance'] + tracks['backSightDistance']).max()
        PIX2METER = road_length / img_width
        carCenterX = carCenterXm / PIX2METER
        carCenterY = carCenterYm / PIX2METER
        bb1X = bb1Xm / PIX2METER
        bb1Y = bb1Ym / PIX2METER
        bb2X = bb2Xm / PIX2METER
        bb2Y = bb2Ym / PIX2METER
        bb3X = bb3Xm / PIX2METER
        bb3Y = bb3Ym / PIX2METER
        bb4X = bb4Xm / PIX2METER
        bb4Y = bb4Ym / PIX2METER

        # Build standard format DataFrame
        # Column order follows NBDT TrajectoryDataFormat wiki specification
        result = pd.DataFrame({
            'frameNum': tracks['frame'],
            'carId': tracks['id'],
            # Pixel coordinates (on highway background image)
            'carCenterX': carCenterX,
            'carCenterY': carCenterY,
            'boundingBox1X': bb1X,
            'boundingBox1Y': bb1Y,
            'boundingBox2X': bb2X,
            'boundingBox2Y': bb2Y,
            'boundingBox3X': bb3X,
            'boundingBox3Y': bb3Y,
            'boundingBox4X': bb4X,
            'boundingBox4Y': bb4Y,
            # Meter coordinates
            'carCenterXm': carCenterXm,
            'carCenterYm': carCenterYm,
            'boundingBox1Xm': bb1Xm,
            'boundingBox1Ym': bb1Ym,
            'boundingBox2Xm': bb2Xm,
            'boundingBox2Ym': bb2Ym,
            'boundingBox3Xm': bb3Xm,
            'boundingBox3Ym': bb3Ym,
            'boundingBox4Xm': bb4Xm,
            'boundingBox4Ym': bb4Ym,
            # Motion attributes
            'heading': heading,
            'course': -1,       # No global north reference in highD
            'speed': speed,
            'objClass': objClass,
            # Geographic coordinates (highD has no GPS data)
            'carCenterLon': -1,
            'carCenterLat': -1,
            # Additional field
            'laneId': tracks['laneId'],
        })

        return result


class InDTransfer(BasicTransfer):
    def __init__(self, args):
        super(InDTransfer, self).__init__(args)

    def _process_data(self, file_path: str) -> pd.DataFrame:
        pass

class NGSIMTransfer(BasicTransfer):

    def __init__(self, args):
        super().__init__(args)

    def get_all_data(self) -> list:
        file_names = sorted(os.listdir(self.args.data_folder))
        data_list = [
            os.path.join(self.args.data_folder, f)
            for f in file_names
            if f.lower().endswith('.csv')
        ]
        return data_list

    @staticmethod
    def _build_local_frame(df: pd.DataFrame):
        FEET2METER = 0.3048
        gx_m = df['Global_X'].values * FEET2METER
        gy_m = df['Global_Y'].values * FEET2METER

        x_origin = gx_m.min()   # x = 0
        y_origin = gy_m.max()   # y = 0

        local_x_m =  (gx_m - x_origin)
        local_y_m = -(gy_m - y_origin)

        return local_x_m, local_y_m, (x_origin, y_origin)

    @staticmethod
    def _compute_heading_and_course(df: pd.DataFrame,
                                    local_x_m: np.ndarray,
                                    local_y_m: np.ndarray,
                                    max_frame_gap: int = 5) -> tuple:
        FEET2METER = 0.3048
        gx_m = df['Global_X'].values * FEET2METER
        gy_m = df['Global_Y'].values * FEET2METER
        vid = df['Vehicle_ID'].values
        fnum = df['Frame_ID'].values

        n = len(df)
        heading = np.full(n, -1.0)
        course = np.full(n, -1.0)

        for i in range(n):
            has_next = (i + 1 < n and vid[i + 1] == vid[i]
                        and abs(fnum[i + 1] - fnum[i]) <= max_frame_gap)
            has_prev = (i - 1 >= 0 and vid[i - 1] == vid[i]
                        and abs(fnum[i] - fnum[i - 1]) <= max_frame_gap)

            if has_next:
                curr, ref = i, i + 1
            elif has_prev:
                curr, ref = i - 1, i
            else:
                continue  

            dx_img = local_x_m[ref] - local_x_m[curr]
            dy_img = local_y_m[ref] - local_y_m[curr]
            heading[i] = np.degrees(np.arctan2(dy_img, dx_img)) % 360

            dE = gx_m[ref] - gx_m[curr]
            dN = gy_m[ref] - gy_m[curr]
            course[i] = np.degrees(np.arctan2(dE, dN)) % 360

        return heading, course

    @staticmethod
    def _oriented_bbox(cx_m, cy_m, length_m, width_m, heading_deg):
        l = length_m / 2
        w = width_m  / 2
        theta = np.radians(heading_deg)
        cos_t, sin_t = np.cos(theta), np.sin(theta)

        lc, ls = l * cos_t, l * sin_t
        wc, ws = w * cos_t, w * sin_t

        bb1Xm = cx_m + lc + ws
        bb1Ym = cy_m + ls - wc
        bb2Xm = cx_m + lc - ws
        bb2Ym = cy_m + ls + wc
        bb3Xm = cx_m - lc - ws
        bb3Ym = cy_m - ls + wc
        bb4Xm = cx_m - lc + ws
        bb4Ym = cy_m - ls - wc

        return bb1Xm, bb1Ym, bb2Xm, bb2Ym, bb3Xm, bb3Ym, bb4Xm, bb4Ym


    def _process_data(self, file_path: str) -> pd.DataFrame:
        raw = pd.read_csv(file_path)
        raw.columns = raw.columns.str.strip()

        raw = raw.sort_values(['Vehicle_ID', 'Frame_ID']).reset_index(drop=True)
        FEET2METER = 0.3048
        length_m = raw['v_length'].values * FEET2METER   # vehicle length (m)
        width_m  = raw['v_Width'].values  * FEET2METER   # vehicle width  (m)
        speed_fps = raw['v_Vel'].values                   # feet/s
        speed_ms  = speed_fps * FEET2METER                # m/s

        local_x_m, local_y_m, origin = self._build_local_frame(raw)
        carCenterXm = local_x_m
        carCenterYm = local_y_m

        heading, course = self._compute_heading_and_course(
            raw, local_x_m, local_y_m
        )

        (bb1Xm, bb1Ym, bb2Xm, bb2Ym, bb3Xm, bb3Ym,bb4Xm, bb4Ym) = self._oriented_bbox(
             carCenterXm, carCenterYm, length_m, width_m, heading
         )
        PIX2METER_NGSIM = 1.0  # 1 pixel == 1 metre (placeholder)
        carCenterX = carCenterXm / PIX2METER_NGSIM
        carCenterY = carCenterYm / PIX2METER_NGSIM
        bb1X = bb1Xm / PIX2METER_NGSIM
        bb1Y = bb1Ym / PIX2METER_NGSIM
        bb2X = bb2Xm / PIX2METER_NGSIM
        bb2Y = bb2Ym / PIX2METER_NGSIM
        bb3X = bb3Xm / PIX2METER_NGSIM
        bb3Y = bb3Ym / PIX2METER_NGSIM
        bb4X = bb4Xm / PIX2METER_NGSIM
        bb4Y = bb4Ym / PIX2METER_NGSIM

        # Map vehicle class
        NGSIM_CLASS_MAP = {
            1: 4,  # motorcycle
            2: 0,  # auto → car
            3: 3,  # truck
        }
        objClass = raw['v_Class'].map(NGSIM_CLASS_MAP).fillna(-1).astype(int)

        result = pd.DataFrame({
            'frameNum':       raw['Frame_ID'],
            'carId':          raw['Vehicle_ID'],
            'laneId':         raw['Lane_ID'],
            'carCenterX':     carCenterX,
            'carCenterY':     carCenterY,
            'boundingBox1X':  bb1X,
            'boundingBox1Y':  bb1Y,
            'boundingBox2X':  bb2X,
            'boundingBox2Y':  bb2Y,
            'boundingBox3X':  bb3X,
            'boundingBox3Y':  bb3Y,
            'boundingBox4X':  bb4X,
            'boundingBox4Y':  bb4Y,
            # Metre coordinates
            'carCenterXm':    carCenterXm,
            'carCenterYm':    carCenterYm,
            'boundingBox1Xm': bb1Xm,
            'boundingBox1Ym': bb1Ym,
            'boundingBox2Xm': bb2Xm,
            'boundingBox2Ym': bb2Ym,
            'boundingBox3Xm': bb3Xm,
            'boundingBox3Ym': bb3Ym,
            'boundingBox4Xm': bb4Xm,
            'boundingBox4Ym': bb4Ym,
            # Motion
            'heading':        heading,
            'course':         course,
            'speed':          speed_ms,
            'objClass':       objClass,
            # Geographic
            'carCenterLon':   -1,
            'carCenterLat':   -1,
        })

        return result
