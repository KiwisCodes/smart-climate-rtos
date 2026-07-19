# Smart Climate Control System (RTOS Project)

This repository implements the Smart Climate Control System for the YoloUNO (ESP32-S3) platform. To keep compilation and deployment simple, the entire system is contained in a single python file: `main.py`.

## System Overview
- **Platform**: YoloUNO (ESP32-S3)
- **Sensor**: DHT20 (I2C, temperature + humidity)
- **Display**: LCD1602 (I2C)
- **Actuators**: 3x RGB LED modules (Heater / Cooler / Humidifier)
- **RTOS Engine**: Custom `asyncio`-compatible event loop using a hand-rolled counting `Semaphore` and a bounded `Queue`.

---

## Code Structure & Ownership in `main.py`

The implementation in `main.py` is divided into logical blocks with developer designations to avoid merge conflicts:

| Developer | Responsibility | Code Section / Functions |
| :--- | :--- | :--- |
| **A — Phan Thanh Hung (10423051)** | RTOS Primitives, Hardware, Main Loop | `Semaphore`, `Queue` (scaffolded), constants, hardware config, helpers, `startup_self_test`, `setup`, `main` |
| **B — Duong Quy Trang (10423110)** | Sensor & LCD Display | `SensorReading` class (scaffolded), `task_read_sensor`, `task_lcd_display` |
| **C — Phan Anh Minh (10423191)**  | Heater & Cooler Actors | `task_heater` (4-state logic), `task_cooler` (2-state cycle) |
| **D — Ngo Anh Hieu (10423195)**   | Humidifier Actor | `task_blinky`, `task_humidifier` (3-stage sequence) |

---

## Deployment to YoloUNO

To deploy onto the ESP32-S3 board:
1. Ensure the board contains the required library files (`yolo_uno.py`, `pins.py`, `lcd1602.py`, `dht20.py`) inside its internal root or `lib` folder.
2. Upload the single `main.py` file to the root of the board.
3. Run `main.py` using your MicroPython IDE (such as Thonny or agy CLI).
