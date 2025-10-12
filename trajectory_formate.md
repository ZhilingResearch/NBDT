# Unified Trajectory Formate
## Metadata

| Name | discription | Unit |
| ----- | ----------- | --- |
| fileName | File name | - |
| recordingDate | Recording date of the file (yyyy:mm:dd) | - |
| weekDay | The day in week day | - |
| recordingTime | Recording time of the file (hh:mm) | - |
| recordingFrameRate | Frame rate of the drone video used to extract the trajectories | Frames Per Second |
| totalFrames | Total number of frames in the file | - |
| duration | Duration of the file | second |
| map | Bird's-eye view map corresponding to the site | - |

## Formate

| Name | discription | Unit |
| ---- | ----------- | ---- |
| frameNum | Frame number of the vehicle waypoint captured at 30 frames per second | - |
| carId | Vehicle unique identifier that remains consistent for all vehicle waypoints across the entire video | - |
| carCenterX | x-coordinate of vehicle bounding box center point | meter |
| carCenterY | y-coordinate of vehicle bounding box center point | meter |
| length | Vehicle length | meter |
| width | Vehicle width | meter |
| heading | Vehicle waypoint heading relative to the global North | Degrees (360 in total) |
| course | Vehicle waypoint heading relative to the image coordinate X-axis | Degrees (360 in total) |
| speed | Vehicle waypoint speed | Meters per second |
| vehicleType | Vehicle type, -1 is undifferentiated, 0 is car, 1 is taxi, 2 is bus, 3 is truck, 4 is motorcycle | - |
| carCenterLon\* | Global longitude of vehicle bounding box center point | Degrees |
| carCenterLat\* | Global latitude of vehicle bounding box center point | Degrees |

## Intermediate variables

(这些数据可能在统一格式的时候会需要。)

|label | discription |
|------| ----------- |
| imgLon\*1, imgLat\*1 | The latitude and longitude coordinates of the corner point 1 of the aerial video |
| imgLon\*2, imgLat\*2 | The latitude and longitude coordinates of the corner point 2 of the aerial video |
| imgLon\*3, imgLat\*3 | The latitude and longitude coordinates of the corner point 3 of the aerial video |
| imgLon\*4, imgLat\*4 | The latitude and longitude coordinates of the corner point 4 of the aerial video |
| pix2meter | The conversion factor k of the pixels of the bird eye view map to meters，k pixel = 1 meter |

# Items included in existing datasets

1 means it can be obtained in the data, 0.5 means it can be obtained after processing, and 0 means it is not included

| Feature        | Citysim | UTE | NGSIM | pNUMA | INTERACTION | ZEN | ROCO | SIND | DLP | I-24 MOTION | 100NDS | highD | inD | roundD |
|----------------|:-------:|:---:|:-----:|:-----:|:------------:|:---:|:----:|:----:|:---:|:------------:|:------:|:-----:|:---:|:------:|
| frameNum       | 1 | 1 | 1 | 1 | 1 | - | 1 | - | - | 1 | - | 1 | 1 | 1 |
| laneId         | 1 | 1 | 0 | 0 | 0 | - | 0 | - | - | 0.5 | - | 1 | 1 | 1 |
| carId          | 1 | 1 | 1 | 1 | 1 | - | 1 | - | - | 1 | - | 1 | 1 | 1 |
| carCenterX     | 1 | 0.5 | 1 | 0.5 | 1 | - | 1 | - | - | 1 | - | 1 | 1 | 1 |
| carCenterY     | 1 | 0.5 | 1 | 0.5 | 1 | - | 1 | - | - | 1 | - | 1 | 1 | 1 |
| length         | 1 | 1 | 1 | 0 | 1 | - | 1 | - | - | 1 | - | 1 | 1 | 1 |
| width          | 1 | 1 | 1 | 0 | 1 | - | 1 | - | - | 1 | - | 1 | 1 | 1 |
| heading        | 1 | 0 | 0 | 0.5 | 1 | - | 1 | - | - | 0 | - | 0 | 1 | 1 |
| course         | 1 | 1 | 0.5 | 0 | 0 | - | 0 | - | - | 0 | - | 0.5 | 1 | 1 |
| speed          | 1 | 1 | 1 | 1 | 1 | - | 1 | - | - | 0 | - | 1 | 1 | 1 |
| vehicle type   | 0 | 0 | 1 | 1 | 1 | - | 1 | - | - | 1 | - | 1 | 1 | 1 |
| carCenterLat   | 1 | 0 | 0 | 1 | 0 | - | 1 | - | - | 0 | - | 0 | 1 | 1 |
| carCenterLon   | 1 | 0 | 0 | 1 | 0 | - | 1 | - | - | 0 | - | 0 | 1 | 1 |

