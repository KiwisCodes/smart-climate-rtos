# Smart Climate Control System (RTOS Project)

This repository implements the Smart Climate Control System for the YoloUNO platform. The entire system is consolidated into a single python file, `main.py`, matching the requirements for testing in the OhSTEM simulation environment.

## System Overview
- **Platform**: YoloUNO (ESP32-S3)
- **Sensor**: DHT20 (Simulated temperature + humidity)
- **Display**: LCD1602 (Simulated text display)
- **Actuators**: 3x RGB LED modules (Simulated Heater / Cooler / Humidifier)
- **RTOS Engine**: Custom `asyncio`-compatible event loop using a hand-rolled counting `Semaphore` and a bounded `Queue`.

---

## Code Structure & Ownership in `main.py`

The implementation in `main.py` is divided into logical blocks with developer designations to document individual contributions:

| Developer | Responsibility | Code Section / Functions |
| :--- | :--- | :--- |
| **A — Phan Thanh Hung (10423051)** | RTOS Primitives, Hardware, Main Loop | `Semaphore`, `Queue`, constants, hardware config, helpers, `startup_self_test`, `setup`, `main` |
| **B — Duong Quy Trang (10423110)** | Sensor & LCD Display | `SensorReading` class, `task_read_sensor`, `task_lcd_display` |
| **C — Phan Anh Minh (10423191)**  | Heater & Cooler Actors | `task_heater` (4-state logic), `task_cooler` (2-state cycle) |
| **D — Ngo Anh Hieu (10423195)**   | Humidifier Actor | `task_blinky`, `task_humidifier` (3-stage sequence) |

---

## Running in the OhSTEM Simulation Environment

To run and verify this code in the teacher's OhSTEM simulator:

1. Open the [OhSTEM VR Simulator Portal](https://app.ohstem.vn/#!/vr) in your web browser.
2. Select **Yolo:UNO** as your target device.
3. Switch the programming mode from blocks to **Python** (using the toggle at the top of the interface).
4. Open the project's [main.py](file:///Users/apple/Coding-projects/smart-climate-rtos/main.py) and copy the entire code contents.
5. Paste the code into the OhSTEM online Python editor.
6. Click the **Run** button to launch the simulator.
7. Observe the logs in the simulated serial terminal and verify that the virtual LCD1602 and RGB LEDs transition states correctly based on your simulated DHT20 readings.
