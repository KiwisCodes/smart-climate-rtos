"""
Smart Climate Control System (RTOS Project)
Platform : YoloUNO (ESP32-S3)
Sensor   : DHT20 (I2C, temperature + humidity)
Display  : LCD1602
Actuators: 3x RGB LED modules (Heater / Cooler / Humidifier)

This consolidated file is split into logical sections. Each section designates the 
responsible group member. Implementable functions and classes are annotated with TODOs.
"""

from yolo_uno import *
from pins import *
from lcd1602 import *
from dht20 import *
import asyncio

# ==============================================================================
# SECTION A: RTOS Primitives, Configuration, & Hardware Init
# Owner: Phan Thanh Hung (10423051)
# ==============================================================================

class Semaphore:
    """
    Teacher-provided custom polling counting semaphore.
    Do not modify.
    """
    def __init__(self, value=1):
        if value < 0:
            raise ValueError("ValueError")
        self.value = value
        self.waiting = []  # List of tokens

    async def acquire(self):
        if self.value > 0:
            self.value -= 1
            return True
        
        curr_task = asyncio.current_task() if hasattr(asyncio, 'current_task') else None
        self.waiting.append(curr_task)
        
        # Create an event for waiting
        ev = asyncio.Event()
        async def wait_placeholder():
            await ev.wait()
            
        # Pending loop
        while self.value <= 0:
            await asleep_ms(10)  # Wait until token is released
            if curr_task not in self.waiting: 
                break
                
        self.value -= 1
        return True

    def release(self):
        self.value += 1
        if self.waiting:
            # Release a token
            task = self.waiting.pop(0)


class Queue:
    """
    Custom bounded Queue, built on top of Semaphore.
    Implements the classic bounded-buffer producer/consumer pattern.
    
    Owner: Person A (Phan Thanh Hung)
    """
    def __init__(self, max_items=5):
        self.items = []
        self.max_items = max_items
        self.item_ready = Semaphore(0)
        self.free_slots = Semaphore(max_items)

    async def put(self, item):
        await self.free_slots.acquire()   # wait for room
        self.items.append(item)
        self.item_ready.release()         # signal: one more item available

    async def get(self):
        await self.item_ready.acquire()   # wait for an item
        item = self.items.pop(0)
        self.free_slots.release()         # signal: one more slot free
        return item

    def empty(self):
        return len(self.items) == 0


# ----------------------------------------------------------------------
# Configuration Thresholds & Timings
# ----------------------------------------------------------------------
TEMP_COLD_CRITICAL_C = 15.0     # Below this: RED (critical cold)
TEMP_COLD_WARNING_C  = 20.0     # [15, 20): ORANGE (cold warning)
TEMP_SAFE_MAX_C      = 28.0     # [20, 28]: GREEN (safe range); >28: heater off
HUMIDITY_THRESHOLD_PCT = 40.0   # Below this: start humidifier sequence

SERIAL_PRINT_INTERVAL_MS = 5000 # Sensor read / print cadence (5s)
BLINK_INTERVAL_MS        = 1000 # Onboard LED heartbeat

COOLER_ACTIVE_MS   = 5000       # Cooler stays "on" this long, then re-checks

HUMIDIFIER_GREEN_MS  = 5000     # Stage 1
HUMIDIFIER_YELLOW_MS = 3000     # Stage 2
HUMIDIFIER_RED_MS    = 2000     # Stage 3

MAX_ITEMS = 5                   # Queue capacity limit

# ----------------------------------------------------------------------
# Hardware Initialisation
# ----------------------------------------------------------------------
led_D13 = Pins(D13_PIN)              # Heartbeat pin indicator

heater_led = RGBLed(D3_PIN, 2)       # Actuator 1: Heater
cooler_led = RGBLed(D5_PIN, 2)       # Actuator 2: Cooler
humidifier_led = RGBLed(D7_PIN, 2)   # Actuator 3: Humidifier

lcd1602 = LCD1602()                  # LCD screen
dht20 = DHT20()                      # DHT20 temperature + humidity sensor

# Queues holding SensorReading objects
lcd_queue = Queue(MAX_ITEMS)
heater_queue = Queue(MAX_ITEMS)
cooler_queue = Queue(MAX_ITEMS)
humidifier_queue = Queue(MAX_ITEMS)


def set_actuator_color(pixel_obj, color_hex):
    """
    Helper function to paint both pixels of a dual-LED RGB module the same color.
    
    Args:
        pixel_obj: The RGBLed instance to control.
        color_hex (str): The hexadecimal representation of the color (e.g. '#ff0000').
    """
    rgb = hex_to_rgb(color_hex)
    pixel_obj.show(0, rgb)
    pixel_obj.show(1, rgb)


# ==============================================================================
# SECTION B: Sensor Reading & LCD Display
# Owner: Duong Quy Trang (10423110)
# ==============================================================================

class SensorReading:
    """
    Immutable-by-convention snapshot of one DHT20 reading.
    
    Owner: Person B (Duong Quy Trang)
    """
    __slots__ = ("temperature_c", "humidity_pct", "reading_id")

    def __init__(self, temperature_c, humidity_pct, reading_id):
        """
        # TODO: Initialize the SensorReading object.
        
        Args:
            temperature_c (float): Temperature reading in Celsius.
            humidity_pct (float): Humidity reading in percentage.
            reading_id (int): Incremental identifier for this reading.
        """
        # TODO: Implement initialization here
        self.temperature_c = temperature_c
        self.humidity_pct = humidity_pct
        self.reading_id = reading_id

    def __repr__(self):
        """
        # TODO: Return formatted reading representation.
        Format: "SensorReading(#ID, T=XXC, H=XX%)"
        """
        # TODO: Implement repr here
        return "SensorReading(#{}, T={}C, H={}%)".format(
            self.reading_id, self.temperature_c, self.humidity_pct
        )


async def task_read_sensor():
    """
    # TODO: Implement task_read_sensor.
    
    Required Logic:
    1. Maintain an internal integer `reading_id` starting at 0.
    2. Loop forever:
        a. Retrieve temperature asynchronously (`await dht20.atemperature()`).
        b. Retrieve humidity asynchronously (`await dht20.ahumidity()`).
        c. Increment `reading_id` by 1.
        d. Wrap values inside a `SensorReading` object.
        e. Print output: "TEMP: <temp> C | HUMI: <humi> %"
        f. Push the reading into `lcd_queue`, `heater_queue`, `cooler_queue`, and `humidifier_queue`.
        g. Asynchronously sleep for `SERIAL_PRINT_INTERVAL_MS` (using `asleep_ms`).
    """
    # TODO: Implement sensor reading producer task
    reading_id = 0
    while True:
        temp = await dht20.atemperature()
        humi = await dht20.ahumidity()
        reading_id += 1
        reading = SensorReading(temp, humi, reading_id)
        print("TEMP:", reading.temperature_c, "C | HUMI:", reading.humidity_pct, "%")
        await lcd_queue.put(reading)
        await heater_queue.put(reading)
        await cooler_queue.put(reading)
        await humidifier_queue.put(reading)

        await asleep_ms(SERIAL_PRINT_INTERVAL_MS)


async def task_lcd_display():
    """
    # TODO: Implement task_lcd_display.
    
    Required Logic:
    1. Loop forever:
        a. Dequeue a reading from `lcd_queue` (`await lcd_queue.get()`).
        b. Clear the screen (`lcd1602.clear()`).
        c. Show temperature on row 0:
           - "TEMP: " at column 0
           - Temperature value string at column 8
           - Degree symbol `chr(0)` at column 13
           - "C" at column 14
        d. Show humidity on row 1:
           - "HUMI: " at column 0
           - Humidity value string at column 8
           - "%" at column 13
    """
    # TODO: Implement LCD display task
    while True:
        reading = await lcd_queue.get()

        lcd1602.clear()
        lcd1602.show('TEMP: ', 0, 0)
        lcd1602.show(str(reading.temperature_c), 0, 8)
        lcd1602.show(chr(0), 0, 13)
        lcd1602.show('C', 0, 14)
        lcd1602.show('HUMI: ', 1, 0)
        lcd1602.show(str(reading.humidity_pct), 1, 8)
        lcd1602.show('%', 1, 13)



# ==============================================================================
# SECTION C: Heater & Cooler Control
# Owner: Phan Anh Minh (10423191)
# ==============================================================================

async def task_heater():
    """    
    Loop forever:
        a. Dequeue a reading from `heater_queue` (`await heater_queue.get()`).
        b. Inspect `temperature_c`:
           - If temp < `TEMP_COLD_CRITICAL_C`: set LED color to RED ('#ff0000').
           - If `TEMP_COLD_CRITICAL_C` <= temp < `TEMP_COLD_WARNING_C`: set LED color to ORANGE ('#ff8c00').
           - If `TEMP_COLD_WARNING_C` <= temp <= `TEMP_SAFE_MAX_C`: set LED color to GREEN ('#00ff00').
           - If temp > `TEMP_SAFE_MAX_C`: turn off LED (set to '#000000').
    """
    while True:
        reading = await heater_queue.get()
        temp = reading.temperature_c

        if temp < TEMP_COLD_CRITICAL_C:
            set_actuator_color(heater_led, '#ff0000')      # RED: critical cold
        elif temp < TEMP_COLD_WARNING_C:
            set_actuator_color(heater_led, '#ff8c00')      # ORANGE: cold warning
        elif temp <= TEMP_SAFE_MAX_C:
            set_actuator_color(heater_led, '#00ff00')      # GREEN: safe range
        else:
            set_actuator_color(heater_led, '#000000')      # OFF: too warm

async def task_cooler():
    """    
    Required Logic:
    1. Loop forever:
        a. Dequeue a reading from `cooler_queue` (`await cooler_queue.get()`).
        b. Inspect `temperature_c`:
           - If temp > `TEMP_SAFE_MAX_C`:
             i. Turn cooler LED to GREEN ('#00ff00').
             ii. Sleep asynchronously for `COOLER_ACTIVE_MS`.
             iii. Turn cooler LED back to BLACK ('#000000') (idle).
           - Otherwise:
             Turn cooler LED to BLACK ('#000000').
    """
    while True:
        reading = await cooler_queue.get()
        temp = reading.temperature_c

        if temp > TEMP_SAFE_MAX_C:
            set_actuator_color(cooler_led, '#00ff00')     # COOLING
            await asleep_ms(COOLER_ACTIVE_MS)
            set_actuator_color(cooler_led, '#000000')      # back to IDLE
        else:
            set_actuator_color(cooler_led, '#000000')      # IDLE

# ==============================================================================
# SECTION D: Humidifier Control & Heartbeat Blinky
# Owner: Ngo Anh Hieu (10423195)
# ==============================================================================

async def task_blinky():
    while True:
        led_D13.toggle()
        await asleep_ms(BLINK_INTERVAL_MS)


async def task_humidifier():
    while True:
        reading = await humidifier_queue.get()
        humi = reading.humidity_pct

        if humi < HUMIDITY_THRESHOLD_PCT:
            set_actuator_color(humidifier_led, '#00ff00')  # Stage 1: GREEN
            await asleep_ms(HUMIDIFIER_GREEN_MS)

            set_actuator_color(humidifier_led, '#ffff00')  # Stage 2: YELLOW
            await asleep_ms(HUMIDIFIER_YELLOW_MS)

            set_actuator_color(humidifier_led, '#ff0000')  # Stage 3: RED
            await asleep_ms(HUMIDIFIER_RED_MS)

            set_actuator_color(humidifier_led, '#000000')  # back to IDLE
        else:
            set_actuator_color(humidifier_led, '#000000')  # IDLE


# ==============================================================================
# SECTION A: Startup Self-Test & Event Loop Setup
# Owner: Phan Thanh Hung (10423051)
# ==============================================================================

async def startup_self_test():
    """
    Hardware startup self-test.
    Briefly lights each actuator LED white, then off, one at a time.
    """
    for led in (heater_led, cooler_led, humidifier_led):
        set_actuator_color(led, '#ffffff')
        await asleep_ms(300)
        set_actuator_color(led, '#000000')


async def setup():
    """
    Firmware setup logic. Starts all task runners.
    """
    print('App started')
    await startup_self_test()
    create_task(task_blinky())
    create_task(task_read_sensor())
    create_task(task_lcd_display())
    create_task(task_heater())
    create_task(task_cooler())
    create_task(task_humidifier())


async def main():
    """
    Main loop keeping the async scheduler alive.
    """
    await setup()
    while True:
        await asleep_ms(100)


run_loop(main())
