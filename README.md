# Cerebri

[![Build](https://github.com/Agroecology-Lab/cerebri/actions/workflows/build.yml/badge.svg)](https://github.com/Agroecology-Lab/cerebri/actions/workflows/build.yml)

See [documentation](https://cognipilot.org/).


# Cerebri Roadmap

Fork target: [NXP FRDM-A-S32K358](https://www.nxp.com/design/design-center/development-boards-and-designs/FRDM-A-S32K358) on Zephyr, acting as a hardware-separated
safety core between the ROS 2 host and the ODrive/CAN actuators — the
same role panda plays in openpilot (host sets intent, MCU enforces limits
and can override it independently).

| # | Feature | Status |
|---|---------|--------|
| C1 | ZROS pub/sub core | Done |
| C2 | Synapse topic/protobuf layer | Done |
| C3 | ODrive CAN actuate driver | Done |
| C4 | VESC CAN / PWM / DShot actuate drivers | Done |
| C5 | Basic safety status publisher (`sense/safety`) — flags SAFE/not, no polygon logic, no override | Done (basic) |
| C6 | FRDM-A-S32K358 board support | Patches submitted (not yet merged/tested on hardware); several TODOs on pin mapping, memory map and debug probe support |
| C7 | GNSS sense task (UBX/NMEA over UART) | Not started |
| C8 | Geofence monitor & safety task — polygon memory, checks position every tick, direct CAN override/stop to actuators | Not started |
| C9 | Stored ENU polygon memory on MCU | Not started |
| C10 | Host-side WGS84→ENU mission planner | Not started — likely belongs in `feldfreund_devkit_ros`, not this repo |
| C11 | NTRIP client + RTCM3 pass-through | Not started — same cross-repo note as C10 |
| C12 | Synapse ROS bridge (protobuf over Ethernet) | Partial — MCU side (`drivers/synapse`) exists, host-side bridge doesn't |
| C13 | Safety test suite for the override path | Not started — needed before C8 ships |

## Notes 

Safety and Testing

* openpilot observes [ISO26262](https://en.wikipedia.org/wiki/ISO_26262) guidelines, see [SAFETY.md](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md) for more details.
* openpilot has software-in-the-loop [tests](https://github.com/commaai/openpilot/blob/master/.github/workflows/tests.yaml) that run on every commit.
* The code enforcing the safety model lives in panda and is written in C, see [code rigor](https://github.com/commaai/panda#code-rigor) for more details.
* panda has software-in-the-loop [safety tests](https://github.com/commaai/panda/tree/master/tests/safety).
* Internally, we have a hardware-in-the-loop Jenkins test suite that builds and unit tests the various processes.
* panda has additional hardware-in-the-loop [tests](https://github.com/commaai/panda/blob/master/Jenkinsfile).
