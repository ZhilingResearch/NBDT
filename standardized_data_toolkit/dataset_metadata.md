# Dataset Metadata

This document organizes the **Meta Data** and **Intermediate Variables** for 8 trajectory datasets (CitySim, highD, inD, rounD, NGSIM, ADAS single-vehicle, ADAS two-vehicle, OpenACC). Format reference: [TrajectoryDataFormat Wiki](https://github.com/ZhilingResearch/Ozone/wiki/TrajectoryDataFormat).

---

## 1. CitySim

**Application Page**: https://github.com/UCF-SST-Lab/UCF-SST-CitySim1-Dataset

**Data Source**: University of Central Florida (UCF), USA / Partner universities (Southwest Jiaotong University, Southeast University, Hong Kong Polytechnic University)

### 1.1 Meta Data

| Field | Value |
|-------|-------|
| datasetName | CitySim |
| siteName | See site list below |
| recordingDate | 2022-03-03 ~ 2022-11-29 (see recording details below) |
| weekDay | Sun, Mon, Wed, Thu, Fri, Sat (see recording details below) |
| localWeather | See recording details below |
| recordingTime | See recording details below |
| recordingFrameRate | 30 FPS |
| totalFrames | See recording details below |
| duration | ~977 minutes of drone video in total |
| map | Per-scene background maps in `main/CitySim/` |
| laneRange | laneId field available in data |

**Site List** (13 scenes):

| Scene | Road Type | Location | Country |
|-------|-----------|----------|---------|
| IntersectionA | Intersection (University@Alafaya, Signalized) | Orlando, FL | USA |
| IntersectionB | Intersection (McCulloch@Seminole, Non-signalized) | Orlando, FL | USA |
| IntersectionC | Intersection (University@McCulloch, Signalized) | Orlando, FL | USA |
| IntersectionD | Intersection (GarageC, Consecutive signalized) | Orlando, FL | USA |
| IntersectionE | Intersection (county@oviedo, Permissive left turn phasing) | Oviedo, FL | USA |
| IntersectionF | Intersection (Publix, Non-signalized) | Orlando, FL | USA |
| RoundaboutA | Roundabout (Tampa, Single lane) | Tampa, FL | USA |
| RoundaboutB | Roundabout (WaterForLake, Two lane) | Orlando, FL | USA |
| ExpresswayA | Expressway (Weaving segment) | Chengdu (SWJTU) | China |
| ExpresswayB | Expressway (Weaving segment) | Nanjing (SEU) | China |
| FreewayB | Freeway (Basic segment) | Chengdu (SWJTU) | China |
| FreewayC | Freeway (Merge/diverge) | Chengdu (SWJTU) | China |
| FreewayD | Freeway (Merge/diverge) | Hong Kong (PolyU) | China |

**Recording Details** (per-scene, per-day):

> Note: Dates were decoded from recording filenames (e.g. `031822Pm02` → 2022-03-18 PM). Time information is from the `data processing.xlsx`. Weather was looked up from [timeanddate.com](https://www.timeanddate.com) historical records for each location and date.

**ExpresswayA** (Chengdu, China):

| Date | WeekDay | startTime | Duration (min) | localWeather |
|------|---------|-----------|----------------|-------------|
| 2022-03-18 | Friday | 17:15 | 66 | Sunny |
| 2022-03-19 | Saturday | 08:16 | 66 | Passing clouds |

**FreewayB** (Chengdu, China):

| Date | WeekDay | startTime | Duration (min) | localWeather |
|------|---------|-----------|----------------|-------------|
| 2022-06-05 | Sunday | 05:15 | 34 | Sunny |

**FreewayC** (Chengdu, China):

| Date | WeekDay | startTime | Duration (min) | localWeather |
|------|---------|-----------|----------------|-------------|
| 2022-06-05 | Sunday | 05:40 | 23 | Sunny |
| 2022-06-09 | Thursday | 05:15 | 39 | Fog / Scattered clouds |

**IntersectionA / University@Alafaya** (Orlando, FL, USA):

| Date | WeekDay | startTime | Duration (min) | localWeather |
|------|---------|-----------|----------------|-------------|
| 2022-03-03 | Thursday | 17:40 | 60 | Sunny |

**IntersectionB / McCulloch@Seminole** (Orlando, FL, USA):

| Date | WeekDay | startTime | Duration (min) | localWeather |
|------|---------|-----------|----------------|-------------|
| — | — | 17:30 | 50 | — |

> Note: IntersectionB recording filenames do not encode date information; date and weather are unknown.

**IntersectionD / GarageC** (Orlando, FL, USA):

| Date | WeekDay | startTime | Duration (min) | localWeather |
|------|---------|-----------|----------------|-------------|
| 2022-03-16 | Wednesday | 17:30 | 15 | Partly sunny |

**IntersectionD V2 / GarageC V2** (Orlando, FL, USA):

| Date | WeekDay | startTime | Duration (min) | localWeather |
|------|---------|-----------|----------------|-------------|
| 2022-03-16 | Wednesday | AM | 99 | Partly sunny |
| 2022-05-30 | Monday | AM | 58 | Mostly sunny |

**IntersectionE / county@oviedo** (Oviedo, FL, USA):

| Date | WeekDay | startTime | Duration (min) | localWeather |
|------|---------|-----------|----------------|-------------|
| 2022-11-18 | Friday | 17:30 | 52 | Sunny |

**IntersectionF / Publix** (Orlando, FL, USA):

| Date | WeekDay | startTime | Duration (min) | localWeather |
|------|---------|-----------|----------------|-------------|
| 2022-05-04 | Wednesday | 17:30 | — | Scattered clouds |

**RoundaboutA / TampaRoundabout** (Tampa, FL, USA):

| Date | WeekDay | startTime | Duration (min) | localWeather |
|------|---------|-----------|----------------|-------------|
| 2022-11-29 | Tuesday | AM | 115 | Sunny |

**RoundaboutB / WaterForLake** (Orlando, FL, USA):

| Date | WeekDay | startTime | Duration (min) | localWeather |
|------|---------|-----------|----------------|-------------|
| 2022-11-18 | Friday | 17:30 | 60 | Sunny |

**Other scenes** (DDI, I-4 Express Lane Exit, ExpresswayB, FreewayD):

| Scene | Date | localWeather | Note |
|-------|------|-------------|------|
| DDI | — | — | No date/time in filename |
| I-4 Express Lane Exit | — | — | No date in filename |
| ExpresswayB | — | — | No recordings in data processing spreadsheet |
| FreewayD | — | — | No recordings in data processing spreadsheet |

The coordinate relationship between the provided trajectory position and the base map is shown in the figure.

![CitySim Coordinate System](images/coord_CitySim.png)

### 1.2 Intermediate Variables

| Variable | Value |
|----------|-------|
| pix2meter | ExpresswayA: 17.912853 pixel = 1 meter; other scenes: — |
| imgLon\*1, imgLat\*1 | (no GPS coordinates provided) |
| imgLon\*2, imgLat\*2 | — |
| imgLon\*3, imgLat\*3 | — |
| imgLon\*4, imgLat\*4 | — |

> **Note**: pix2meter was derived from the ratio of pixel coordinates to feet coordinates in the data: `carCenterX (pixel) / (carCenterXft * 0.3048)`, with zero variance (std=0).

---

## 2. highD

**Application Page**: https://levelxdata.com/highd-dataset/

**Data Source**: RWTH Aachen University (ika), German Autobahn

### 2.1 Meta Data

| Field | Value |
|-------|-------|
| datasetName | highD |
| siteName | weisweiler, garzweiler, grevenbroich, bergheim-sud, serways-raststatte, koln-west (Highway, Germany) |
| recordingDate | Sep 2017 – Jul 2018 (month-level precision, see recording details) |
| weekDay | Tue, Thu, Fri, Mon, Wed |
| localWeather | Sunny and windless |
| recordingTime | See recording details table |
| recordingFrameRate | 25 FPS |
| totalFrames | Varies per recording (= duration × 25) |
| duration | 389 – 1251 seconds |
| map | XX_highway.png (one per recording) |
| laneRange | upperLaneMarkings / lowerLaneMarkings (see recordingMeta) |

**Recording Details** (60 recordings across 11 days):

| month | weekDay | startTime | duration (min) |
|-------|---------|-----------|----------------|
| 9.2017 | Tue | 08:38 | 49 |
| 9.2017 | Thu | 11:16 | 57 |
| 9.2017 | Thu | 16:18 | 62 |
| 9.2017 | Fri | 08:21 | 56 |
| 9.2017 | Fri | 08:49 | 143 |
| 10.2017 | Mon | 08:55 | 182 |
| 10.2017 | Mon | 09:04 | 131 |
| 10.2017 | Wed | 11:26 | 76 |
| 11.2017 | Wed | 08:47 | 144 |
| 1.2018 | Thu | 09:16 | 69 |
| 7.2018 | Wed | 09:15 | 30 |

The coordinate relationship between the provided trajectory position and the base map is shown in the figure.

![highD Coordinate System](images/coord_highD.png)

### 2.2 Intermediate Variables

| Variable | Value |
|----------|-------|
| pix2meter | — |
| imgLon\*1, imgLat\*1 | (highD does not provide GPS coordinates) |
| imgLon\*2, imgLat\*2 | — |
| imgLon\*3, imgLat\*3 | — |
| imgLon\*4, imgLat\*4 | — |

---

## 3. inD

**Application Page**: https://levelxdata.com/ind-dataset/

**Data Source**: RWTH Aachen University (ika), German urban intersections

### 3.1 Meta Data

| Field | Value |
|-------|-------|
| datasetName | inD |
| siteName | Bendplatz, Frankenburg, Heckstrasse, Neukollner Strasse (Intersection, Germany) |
| recordingDate | (dataset only provides weekday, no specific date) |
| weekDay | monday, tuesday, wednesday, thursday |
| localWeather | (pending local historical weather lookup in Aachen, Germany) |
| recordingTime | startTime field (hour of day, see recording details) |
| recordingFrameRate | 25 FPS |
| totalFrames | Varies per recording (= duration × 25) |
| duration | 648 – 1328 seconds |
| map | XX_background.png (one per recording) |
| laneRange | Lanelet map files available (OSM format) |

**Recording Details** (33 recordings across 9 days):

| weekday | startTime | duration (min) | localWeather |
|---------|-----------|----------------|-------------|
| wednesday | 16:00 | 16 | — |
| tuesday | 15:00 | 32 | — |
| monday | 12:00 | 62 | — |
| tuesday | — | 63 | — |
| monday | 16:00 | 67 | — |
| tuesday | 15:00 | 56 | — |
| tuesday | 16:00 | 135 | — |
| wednesday | 16:00 | 107 | — |
| thursday | 13:00 | 51 | — |

The coordinate relationship between the provided trajectory position and the base map is shown in the figure.

![inD Coordinate System](images/coord_inD.png)

### 3.2 Intermediate Variables

| Variable | locationId 1 (Bendplatz) | locationId 2 (Frankenburg) | locationId 3 (Heckstrasse) | locationId 4 (Neukollner Str.) |
|----------|--------------------------|---------------------------|---------------------------|-------------------------------|
| pix2meter | 122.76 | 122.76 | 122.76 | 78.74 |
| xUtmOrigin | 293487.1224 | 295620.9575 | 300127.0853 | 297631.3187 |
| yUtmOrigin | 5629712 | 5628102 | 5629091 | 5629917 |
| latLocation | 50.78207 | 50.76836 | 50.77887 | 50.78505 |
| lonLocation | 6.07116 | 6.10227 | 6.16553 | 6.13070 |
| imgLon\*1–4, imgLat\*1–4 | (to be derived from UTM origin + image size × pix2meter) | — | — | — |


---

## 4. rounD

**Application Page**: https://levelxdata.com/round-dataset/

**Data Source**: RWTH Aachen University (ika), German roundabouts

### 4.1 Meta Data

| Field | Value |
|-------|-------|
| datasetName | rounD |
| siteName | Thiergarten, KackertstraBe, Neuweiler (Roundabout, Germany) |
| recordingDate | (dataset only provides weekday, no specific date) |
| weekDay | tuesday, wednesday, thursday |
| localWeather | (pending local historical weather lookup in Aachen, Germany) |
| recordingTime | startTime field (hour of day, see recording details) |
| recordingFrameRate | 25 FPS |
| totalFrames | Varies per recording (= duration × 25) |
| duration | 441 – 1250 seconds |
| map | XX_background.png (one per recording) |
| laneRange | — |

**Recording Details** (24 recordings across 5 days):

| weekday | startTime | duration (min) | localWeather |
|---------|-----------|----------------|-------------|
| tuesday | 07:00 | 17 | — |
| wednesday | 11:00 | 18 | — |
| thursday | 09:00 | 123 | — |
| tuesday | 09:00 | 166 | — |
| wednesday | 09:00 | 73 | — |

The coordinate relationship between the provided trajectory position and the base map is shown in the figure.

![rounD Coordinate System](images/coord_rounD.png)

### 4.2 Intermediate Variables

| Variable | locationId 0 (Thiergarten) | locationId 1 (KackertstraBe) | locationId 2 (Neuweiler) |
|----------|---------------------------|-----------------------------|-----------------------|
| pix2meter | 98.43 | 67.52 | 73.35 |
| xUtmOrigin | 301221.3650 | 292669.4681 | 296309.7867 |
| yUtmOrigin | 5641501.3410 | 5630731.7040 | 5639851.9642 |
| latLocation | 50.8906 | 50.7906 | 50.8738 |
| lonLocation | 6.1747 | 6.0599 | 6.1066 |
| imgLon\*1–4, imgLat\*1–4 | (to be derived from UTM origin + image size × pix2meter) | — | — |


---

## 5. NGSIM

**Application Page**: https://data.transportation.gov/stories/s/Next-Generation-Simulation-NGSIM-Open-Data/i5zb-xe34/

**Data Source**: U.S. Department of Transportation (FHWA)

### 5.1 Meta Data

| Field | Value |
|-------|-------|
| datasetName | NGSIM |
| siteName | I-80, US-101, Lankershim Blvd, Peachtree St (Freeway / Urban arterial, USA) |
| recordingDate | See recording details below |
| weekDay | See recording details below |
| localWeather | Clear |
| recordingTime | See recording details below |
| recordingFrameRate | 10 FPS (I-80, US-101) / 15 FPS (Lankershim, Peachtree) |
| totalFrames | (no local NGSIM raw data files available) |
| duration | 15 minutes per segment |
| map | See map path below |
| laneRange | Lane_ID field available in data |

**Recording Details** (4 locations):

| Location | recordingDate | weekDay | recordingTime |
|----------|--------------|---------|---------------|
| I-80 | 2005-04-13 | Wednesday | 16:00–16:15, 17:00–17:15, 17:15–17:30 |
| US-101 | 2005-06-15 | Wednesday | 07:50–08:05, 08:05–08:20, 08:20–08:35 |
| Lankershim Blvd | 2005-06-16 | Thursday | 08:30–09:00 |
| Peachtree St | 2006-11-08 | Wednesday | 12:45–13:00, 16:00–16:15 |

The coordinate relationship between the provided trajectory position and the base map is shown in the figure.

![NGSIM Coordinate System](images/coord_NGSIM.png)

### 5.2 Intermediate Variables

| Variable | Value |
|----------|-------|
| pix2meter | — |
| imgLon\*1, imgLat\*1 | (NGSIM raw data uses Global_X/Y in feet, no map corner GPS coordinates) |
| imgLon\*2, imgLat\*2 | — |
| imgLon\*3, imgLat\*3 | — |
| imgLon\*4, imgLat\*4 | — |

---

## 6. ADAS Single-Vehicle (Central Ohio)

**Application Page**: https://data.transportation.gov/Automobiles/Advanced-Driver-Assistance-System-ADAS-/iie8-uenj

**Data Source**: U.S. Department of Transportation, Federal Highway Administration (FHWA) / ITS DataHub

### 6.1 Meta Data

| Field | Value |
|-------|-------|
| datasetName | ADAS_SingleVehicle_Ohio |
| siteName | See corridor list below (Central Ohio route corridors) |
| recordingDate | yyyy-mm-dd |
| weekDay | weekday name (e.g. Monday, Tuesday) |
| localWeather | Per collection: road surface condition — Dry / Wet |
| recordingTime | Per collection: start time `HH:MM` |
| recordingFrameRate | 10 FPS |
| totalFrames | Varies per collection (= duration × 10) |
| duration | Per collection: segment length in seconds |
| map | Google Maps route link, or `-` |
| laneRange | `-` (laneId available in trajectory) |
| corridor | Per collection: route corridor code (see recording details) |
| run_number | Per collection: FHWA run index (1–34) |
| sub_run_number | Per collection: sub-run index (1–2) |
| roadway_type | Per collection: Limited access / Divided / Non-divided arterial |
| aggressiveness | Per collection: SV aggressiveness setting |
| following_distance | Per collection: SV following-distance setting |
| speed_limits | Per collection: speed limits along route (m/s; converted from mph) |
| route_distance | Per collection: route distance (m; converted from miles) |
| map_origin_lon | Per collection: map origin longitude (degrees) |
| map_origin_lat | Per collection: map origin latitude (degrees) |
| map_origin_alt | Per collection: map origin altitude (m) |
| annual_traffic_density | Per collection: AADT along route |

**Recording Details** (216 collections, 2021-09-15 – 2022-02-19; per-corridor, per-day):

> Note: Each collection is one route segment. `recordingTime` is the earliest start time on that date within each corridor; `duration` is the min–max segment length (seconds) among collections on that date.

| recordingDate | weekDay | collections | duration (s) | localWeather |
|---------------|---------|-------------|--------------|--------------|
| 2021-09-15 | Wednesday | 1 | 119.4–119.4 | Dry |
| 2021-09-30 | Thursday | 3 | 209.7–230.5 | Dry |
| 2021-10-01 | Friday | 3 | 180.5–208.2 | Dry |
| 2021-11-15 | Monday | 6 | 239.1–510.2 | Dry |
| 2021-11-16 | Tuesday | 14 | 130.0–1669.7 | Dry |
| 2021-11-18 | Thursday | 1 | 144.6–144.6 | Dry |
| 2021-11-20 | Saturday | 12 | 119.7–204.6 | Dry |
| 2021-11-22 | Monday | 7 | 289.6–409.6 | Dry |
| 2022-01-31 | Monday | 23 | 10.3–289.6 | Dry |
| 2022-02-07 | Monday | 11 | 304.6–454.4 | Wet |
| 2022-02-08 | Tuesday | 16 | 108.9–259.6 | Wet |
| 2022-02-09 | Wednesday | 20 | 93.0–209.7 | Dry |
| 2022-02-10 | Thursday | 10 | 164.6–264.6 | Wet |
| 2022-02-15 | Tuesday | 16 | 219.6–434.6 | Dry |
| 2022-02-16 | Wednesday | 41 | 0.1–289.6 | Dry, Wet |
| 2022-02-18 | Friday | 20 | 233.0–469.6 | Wet |
| 2022-02-19 | Saturday | 12 | 354.6–499.7 | Dry |

> **Note**: `duration` and `totalFrames` vary widely because each collection is one route segment (not one full run). The longest collection is ~1669.7 s (~27.8 min); shortest is ~0.1 s (degenerate segment). Per-collection `totalFrames` ranges from ~2 to ~16,698 at 10 FPS.

**US 315 — Dublin / Columbus corridor** (Dublin – Columbus, OH, USA):

> Limited access (US-315); Wendy's (4555 W Dublin Granville Rd, Dublin) ↔ BP (1090 Dublin Rd, Columbus).

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2021-11-15 | Monday | 12:05 | 239.1–510.2 | Dry | 6 |

**US 33 — Marysville corridor** (Marysville, OH, USA):

> Limited access / non-divided arterial (US-33 / US-42); Kroger Fuel Center (1501 W 5th St) ↔ Marathon Gas (10152 US-42, Marysville).

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2021-09-15 | Wednesday | 16:50 | 119.4 | Dry | 1 |
| 2021-11-16 | Tuesday | 09:38 | 130.0–1669.7 | Dry | 13 |

**US 33 — Dublin / Columbus corridor** (Dublin – Columbus, OH, USA):

> Limited access (US-33); Wendy's (4555 W Dublin Granville Rd, Dublin) ↔ Starbucks (1093 Dublin Rd, Columbus).

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2021-09-30 | Thursday | 13:59 | 209.7–230.5 | Dry | 3 |

**I-270 / I-71 — Columbus metro corridor** (Columbus, OH, USA):

> Limited access / divided arterial; Marathon Gas (700 E N Broadway) ↔ bp (4024 Morse Rd); Columbus metro arterials.

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2021-10-01 | Friday | 09:36 | 180.5–208.2 | Dry | 3 |
| 2021-11-16 | Tuesday | 11:16 | 160.7 | Dry | 1 |
| 2021-11-18 | Thursday | 10:23 | 144.6 | Dry | 1 |
| 2021-11-20 | Saturday | 10:10 | 119.7–204.6 | Dry | 12 |
| 2022-02-08 | Tuesday | 09:45 | 108.9–209.6 | Wet | 4 |
| 2022-02-09 | Wednesday | 09:26 | 93.0–209.7 | Dry | 20 |
| 2022-02-10 | Thursday | 10:02 | 169.1–169.6 | Wet | 2 |
| 2022-02-15 | Tuesday | 09:15 | 219.6–434.6 | Dry | 16 |
| 2022-02-16 | Wednesday | 12:03 | 145.6–289.6 | Dry | 20 |

**US 23 — Delaware / Waldo corridor** (Delaware – Waldo, OH, USA):

> Divided / limited access arterial (US-23); Speedway (2381 U.S. Hwy 23 N, Delaware) ↔ bp (262 N Marion St, Waldo).

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2022-01-31 | Monday | 10:43 | 10.3–289.6 | Dry | 23 |
| 2022-02-16 | Wednesday | 09:44 | 31.7–262.5 | Wet | 20 |

**I-670 / US 33 — Lewis Center / Westerville corridor** (Lewis Center – Westerville, OH, USA):

> Divided arterial (I-670 / US-33); Meijer (8870 Columbus Pike, Lewis Center) ↔ Wendy's (5771 Maxtown Rd, Westerville).

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2022-02-07 | Monday | 10:40 | 304.6–454.4 | Wet | 11 |
| 2022-02-19 | Saturday | 10:54 | 354.6–499.7 | Dry | 12 |

**US 33 — Dublin / Hilliard corridor** (Dublin – Hilliard, OH, USA):

> Non-divided / divided arterial (US-33); Panera Bread (6665 Perimeter Loop Rd, Dublin) ↔ Speedway (3760 Main St, Hilliard).

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2021-11-22 | Monday | 09:46 | 289.6–409.6 | Dry | 7 |
| 2022-02-18 | Friday | 09:21 | 233.0–469.6 | Wet | 20 |

**I-71 / Olentangy — Worthington corridor** (Worthington – Columbus, OH, USA):

> Limited access (I-71 / Olentangy Fwy); Kroger Fresh Fare (Worthington Mall) ↔ I-71 / Olentangy Fwy access.

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2022-02-08 | Tuesday | 09:41 | 164.6–259.6 | Wet | 12 |
| 2022-02-10 | Thursday | 09:42 | 164.6–264.6 | Wet | 8 |

**US 23 — Columbus Summit St corridor** (Columbus, OH, USA):

> Urban arterial (US-23 / Summit St); Used Kids Records (2500 Summit St) ↔ Evolved Body Art (2520 Summit St).

| Corridor | Date | localWeather | Note |
|----------|------|--------------|------|
| US 23 — Columbus Summit St | — | — | Route defined in FHWA documentation; no collections in current export |

**Other / incomplete metadata** (Central Ohio, USA):

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2022-02-16 | Wednesday | 12:03 | 0.1 | — | 1 |

> Note: One collection has missing route endpoint metadata.

Trajectories use **map frame** coordinates (east/north, meters). No background image or pixel calibration is provided.

### 6.2 Intermediate Variables

| Variable | Value |
|----------|-------|
| pix2meter | — (no background image; positions are map-frame meters) |
| coordinateFrame | Map ENU frame (x = east, y = north, m) |
| vehicleRole | 2 (subject vehicle, `carId` 0) / 1 (adjacent vehicle) |
| type_of_vehicle | Appearance/operation — RI / DI / Baseline |
| length, width, height | Vehicle dimensions (m) |

> **Note**: Each `frameNum` has **one** subject-vehicle record (`carId` 0) and **one record per adjacent vehicle** present at that time (`carId` = raw `ID`). Raw CSV rows are expanded per AdjV encounter; the transfer deduplicates so `(frameNum, carId)` is unique. Acceleration is not included. Output folders are named `{corridor}_{YYYYMMDD}_{HHMMSS}_run{run}_sub{sub}` (e.g. `US33_MSV_20210915_165010_run04_sub1`); see `recordings_index.csv` for the full list.

---

## 7. ADAS Two-Vehicle (Central Ohio)

**Application Page**: https://data.transportation.gov/Automobiles/Advanced-Driver-Assistance-System-ADAS-/vhz2-exyi

**Data Source**: U.S. Department of Transportation, Federal Highway Administration (FHWA) / ITS DataHub

### 7.1 Meta Data

| Field | Value |
|-------|-------|
| datasetName | ADAS_TwoVehicle_Ohio |
| siteName | See corridor list below (Central Ohio route corridors) |
| recordingDate | yyyy-mm-dd |
| weekDay | weekday name (e.g. Tuesday, Thursday) |
| localWeather | road surface condition — Dry / Wet |
| recordingTime | Per collection: start time `HH:MM` |
| recordingFrameRate | 10 FPS |
| totalFrames | Varies per collection (= duration × 10) |
| duration | Per collection: segment length in seconds |
| map | Google Maps route link, or `-` |
| laneRange | `-` (laneId available in trajectory) |
| corridor | Per collection: route corridor code |
| run_number | Per collection: FHWA run index |
| sub_run_number | Per collection: sub-run index (1–2) |
| roadway_type | Per collection: e.g. Limited Access |
| aggressiveness | Per collection: SV aggressiveness setting (e.g. Average) |
| following_distance | Per collection: ACC following-distance setting for SV1 (integer level 1–7; FHWA Data Dictionary) |
| speed_limits | Per collection: speed limits along route (m/s; converted from mph) |
| route_distance | Per collection: route distance (m; converted from miles) |
| map_origin_lon | Per collection: map origin longitude (degrees) |
| map_origin_lat | Per collection: map origin latitude (degrees) |
| map_origin_alt | Per collection: map origin altitude (m) |
| gap_level | Per collection: intended gap between SV1 and SV2 — **1** (30–60 m) or **2** (60–80 m) |
| annual_traffic_density | Per collection: AADT along route (e.g. `>50000`) |

**Recording Details** (68 collections, 2022-03-15 – 2022-03-21; per-corridor, per-day):

> Note: Each collection is one route segment with **two** instrumented subject vehicles (SV1, SV2) and adjacent-vehicle tracks. `recordingTime` is the earliest start time on that date within each corridor; `duration` is the min–max segment length (seconds) among collections on that date. All collections in the current export are **Dry**.

| recordingDate | weekDay | collections | duration (s) | localWeather |
|---------------|---------|-------------|--------------|--------------|
| 2022-03-15 | Tuesday | 34 | 82.5–289.4 | Dry |
| 2022-03-17 | Thursday | 15 | 234.6–384.4 | Dry |
| 2022-03-21 | Monday | 19 | 178.0–469.6 | Dry |

> **Note**: `duration` and `totalFrames` vary by segment. Shortest collection is ~82.5 s (~826 frames); longest is ~469.6 s (~4,697 frames) at 10 FPS.

**I-71 / Olentangy — Worthington corridor** (Worthington – Columbus, OH, USA):

> Limited access (I-71 / Olentangy Fwy); bp (660 Neil Ave, Columbus) ↔ Olentangy Fwy / I-71 access.

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2022-03-15 | Tuesday | 09:54 | 82.5–289.4 | Dry | 17 |

**I-270 — Columbus metro loop** (Columbus, OH, USA):

> Limited access; Olentangy Fwy ↔ I-270 ↔ I-71 (Columbus outer belt segments).

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2022-03-15 | Tuesday | 10:09 | 169.3–234.6 | Dry | 17 |

**US 23 — Columbus Summit St corridor** (Columbus, OH, USA):

> Urban arterial (US-23 / Summit St); Used Kids Records (2500 Summit St) ↔ Evolved Body Art (2520 Summit St).

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2022-03-17 | Thursday | 10:43 | 234.6–384.4 | Dry | 15 |

**I-670 / US 33 — Lewis Center / Westerville corridor** (Lewis Center – Westerville, OH, USA):

> Divided arterial (I-670 / US-33); Meijer (8870 Columbus Pike, Lewis Center) ↔ Wendy's (5771 Maxtown Rd, Westerville).

| recordingDate | weekDay | recordingTime | duration (s) | localWeather | collections |
|---------------|---------|---------------|--------------|--------------|-------------|
| 2022-03-21 | Monday | 09:15 | 178.0–469.6 | Dry | 19 |

Trajectories use **map frame** coordinates (east/north, meters). No background image or pixel calibration is provided.

### 7.2 Intermediate Variables

| Variable | Value |
|----------|-------|
| pix2meter | — (no background image; positions are map-frame meters) |
| coordinateFrame | Map ENU frame (x = east, y = north, m) |
| vehicleRole | 2 (subject vehicles, `carId` `0_1` / `0_2`) / 1 (adjacent vehicle) |
| type_of_vehicle | Appearance/operation — RI / DI / Baseline |
| length, width, height | Vehicle dimensions (m) |

> **Note**: Each `frameNum` has **one** SV1 record (`carId` `0_1`), **one** SV2 record (`carId` `0_2`), and **one record per adjacent vehicle** present at that time (`carId` = raw `ID`). Raw CSV rows are expanded per AdjV encounter; the transfer deduplicates so `(frameNum, carId)` is unique. **`following_distance`** and **`gap_level`** are stored in **metadata only** (collection-level experiment settings; not repeated in trajectory). Acceleration is not included. Output folders are named `{corridor}_{YYYYMMDD}_{HHMMSS}_run{run}_sub{sub}` (e.g. `I71_OLE_20220315_104914_run08_sub1`); see `recordings_index.csv` for the full list.

---

## 8. OpenACC (JRC Car-Following Platoon)

**Application Page**: https://data.europa.eu/data/datasets/9702c950-c80f-4d2f-982f-44d06ea0009f?locale=en

**Data Source**: European Commission, Joint Research Centre (JRC) / [JRC OpenACC FTP mirror](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/TransportExpData/JRCDBT0001/LATEST/)

### 8.1 Meta Data

| Field | Value |
|-------|-------|
| datasetName | OpenACC |
| siteName | See campaign list below |
| recordingDate | Experiment date (yyyy-mm-dd) |
| weekDay | Weekday name (e.g. Monday, Tuesday) |
| localWeather | `-` (not available) |
| recordingTime | `-` (not available) |
| recordingFrameRate | 10 FPS |
| totalFrames | Varies (= duration × 10) |
| duration | Platoon segment length in seconds (see recording details) |
| map | Route or proving-ground description (see campaign list) |
| laneRange | `-` (no lane assignment) |
| vehicle_order | Vehicle models in platoon order (leader → follower) |
| number_of_vehicles | Vehicles with valid trajectory in the platoon |
| distance_setting | ACC following time-gap setting — `min`, `max`, `S`, `M`, `L`, `SL`, `shortest`, `second shortest`, `none`, or `-` |
| test_environment | Test site type — `proving_ground`, `public_highway`, or `campus` |
| equipment | Positioning and speed sensing equipment (see campaign list) |

**Campaign List** (6 platoon campaigns, 139 collections in current export, 2018-08-30 – 2020-10-27):

| Campaign | Test environment | Location | Equipment | Typical platoon size |
|----------|------------------|----------|-----------|----------------------|
| AstaZero | Proving ground | AstaZero Rural Road (~5.7 km), Sweden | OxTS RT-Range S | 5 vehicles |
| Casale | Public highway | Ispra – Casale Monferrato, Italy | Ublox 9, OBD | 2 vehicles |
| Cherasco | Public highway | Ispra – Cherasco freeway, Italy | Ublox 8, OBD | 2–3 vehicles |
| JRC low speed | Campus | JRC Ispra territory, Italy | Ublox 9, OBD | 2–3 vehicles |
| Vicolungo | Public highway | Ispra – Vicolungo, Italy | Ublox 8, OBD | 5 vehicles |
| ZalaZone | Proving ground | ZalaZONE Dynamic Platform / Handling Course, Hungary | INVENTURE VBOX, Ublox 9, Tracker App | 4–11 vehicles |

**Recording Details** (139 collections; per-campaign summary):

| Campaign | recordingDate | weekDay | collections | duration (s) |
|----------|---------------|---------|-------------|--------------|
| Cherasco | 2018-08-30 | Thursday | 5 | 144.7–2282.0 |
| Cherasco | 2018-09-24 | Monday | 6 | 486.3–4059.9 |
| Vicolungo | 2019-02-26 – 2019-02-28 | Tue – Thu | 12 | 145.4–1009.6 |
| AstaZero | 2019-07-04 – 2019-07-05 | Thu – Fri | 10 | 905.4–2263.4 |
| ZalaZone | 2019-10-08 – 2019-10-09 | Tue – Wed | 73 | 32.8–757.7 |
| JRC low speed | 2020-09-30 | Wednesday | 24 | 101.5–568.5 |
| Casale | 2020-10-27 | Tuesday | 9 | 100.0–1522.9 |

**AstaZero — Rural Road** (AstaZero, Sweden):

> Proving-ground car-following laps; leader ACC on most runs; platoon size 5.

| recordingDate | weekDay | collections | duration (s) | distance_setting |
|---------------|---------|-------------|--------------|------------------|
| 2019-07-04 | Thursday | 5 | 905.4–1576.9 | `none`, `min`, `max` |
| 2019-07-05 | Friday | 5 | 1576.9–2263.4 | `none`, `min`, `max` |

**Casale — Ispra / Casale Monferrato** (northern Italy):

> Two-vehicle platoon on public roads; follower ACC with occasional manual override.

| recordingDate | weekDay | collections | duration (s) | distance_setting |
|---------------|---------|-------------|--------------|------------------|
| 2020-10-27 | Tuesday | 9 | 100.0–1522.9 | `min` |

**Cherasco — Ispra / Cherasco freeway** (northern Italy):

> Two- or three-vehicle platoons with mixed ACC and manual control; some segments have incomplete motion fields.

| recordingDate | weekDay | collections | duration (s) | distance_setting |
|---------------|---------|-------------|--------------|------------------|
| 2018-08-30 | Thursday | 5 | 144.7–2282.0 | `min` |
| 2018-09-24 | Monday | 6 | 486.3–4059.9 | `min` |

**JRC low speed — Ispra campus** (Italy):

> Low-speed platoon tests on JRC site; 2–3 vehicles; some collections lack per-frame control state (`driver` inferred from experiment settings).

| recordingDate | weekDay | collections | duration (s) | distance_setting |
|---------------|---------|-------------|--------------|------------------|
| 2020-09-30 | Wednesday | 24 | 101.5–568.5 | `shortest`, `second shortest` |

**Vicolungo — Ispra / Vicolungo** (northern Italy):

> Five-vehicle highway platoons.

| recordingDate | weekDay | collections | duration (s) | distance_setting |
|---------------|---------|-------------|--------------|------------------|
| 2019-02-26 | Tuesday | 5 | 145.4–1009.6 | `min` |
| 2019-02-27 | Wednesday | 2 | 724.1–915.7 | `min` |
| 2019-02-28 | Thursday | 5 | 338.2–740.4 | `min` |

**ZalaZone — Proving ground** (Hungary):

> Dynamic Platform (speed perturbations) and Handling Course (constant cruise); ACC time-gap settings include short (`S`), long (`L`), and mixed platoon settings (`SL`).

| recordingDate | weekDay | collections | duration (s) | distance_setting |
|---------------|---------|-------------|--------------|------------------|
| 2019-10-08 | Tuesday | 26 | 32.8–757.7 | `S`, `L`, `SL`, … |
| 2019-10-09 | Wednesday | 47 | 40.4–520.0 | `S`, `L`, `SL`, … |

Trajectories use **map frame** coordinates (east/north, meters). Global positions are in WGS84 (`carCenterLon`/`carCenterLat`, degrees); missing or invalid GNSS → `-1`. Each collection uses an independent local ENU origin. No background image or pixel calibration is provided.

### 8.2 Intermediate Variables

| Variable | Value |
|----------|-------|
| carId | Platoon vehicle index (1, 2, …, N; may be non-contiguous when a vehicle has no data) |
| pix2meter | — (no background image; positions are map-frame meters) |
| coordinateFrame | Map ENU frame (x = east, y = north, m); WGS84 for global lon/lat |
| driver | Manual control (`Human`), ACC (`ACC`), or unknown |
| bbox dimensions | Fixed **4.8 m × 1.8 m** for all vehicles (vehicle dimensions not provided) |

