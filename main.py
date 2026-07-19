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
        """
        # TODO: Initialize the custom bounded Queue.
        
        Required Logic:
        1. Initialize `self.items` as an empty list to store queue elements.
        2. Store the capacity limit in `self.max_items`.
        3. Create `self.item_ready` as a Semaphore initialized to 0 (counts filled slots).
        4. Create `self.free_slots` as a Semaphore initialized to max_items (counts free slots).
        """
        # TODO: Implement initialization here
        raise NotImplementedError("TODO: Person A needs to implement Queue.__init__")

    async def put(self, item):
        """
        # TODO: Put an item into the queue.
        
        Required Logic (Producer side):
        1. Wait for a free slot by acquiring `self.free_slots` (async).
        2. Append `item` to `self.items`.
        3. Signal that a new item is ready by releasing `self.item_ready` (sync).
        
        Args:
            item: The object to put in the queue.
        """
        # TODO: Implement put operation
        raise NotImplementedError("TODO: Person A needs to implement Queue.put")

    async def get(self):
        """
        # TODO: Get and remove an item from the queue.
        
        Required Logic (Consumer side):
        1. Wait until an item is ready by acquiring `self.item_ready` (async).
        2. Remove and return the first item from `self.items` (FIFO).
        3. Signal that a slot has freed up by releasing `self.free_slots` (sync).
        
        Returns:
            The popped item.
        """
        # TODO: Implement get operation
        raise NotImplementedError("TODO: Person A needs to implement Queue.get")

    def empty(self):
        """
        # TODO: Check if the queue is empty.
        
        Returns:
            bool: True if queue has no items.
        """
        # TODO: Implement empty check
        raise NotImplementedError("TODO: Person A needs to implement Queue.empty")


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

# ----------------------------------------------------------------------
# Per-consumer Queues (data hand-off - no shared globals)
# ----------------------------------------------------------------------
# TODO: Once Queue is implemented, these queues will hold SensorReading objects
# lcd_queue = Queue(MAX_ITEMS)
# heater_queue = Queue(MAX_ITEMS)
# cooler_queue = Queue(MAX_ITEMS)
# humidifier_queue = Queue(MAX_ITEMS)


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
        self.reading_id, self.temperature_c, self.humidity_pct )


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
    raise NotImplementedError("TODO: Person B needs to implement task_lcd_display")


# ==============================================================================
# SECTION C: Heater & Cooler Control
# Owner: Phan Anh Minh (10423191)
# ==============================================================================

async def task_heater():
    """
    # TODO: Implement task_heater.
    
    Required Logic:
    1. Loop forever:
        a. Dequeue a reading from `heater_queue` (`await heater_queue.get()`).
        b. Inspect `temperature_c`:
           - If temp < `TEMP_COLD_CRITICAL_C`: set LED color to RED ('#ff0000').
           - If `TEMP_COLD_CRITICAL_C` <= temp < `TEMP_COLD_WARNING_C`: set LED color to ORANGE ('#ff8c00').
           - If `TEMP_COLD_WARNING_C` <= temp <= `TEMP_SAFE_MAX_C`: set LED color to GREEN ('#00ff00').
           - If temp > `TEMP_SAFE_MAX_C`: turn off LED (set to '#000000').
    """
    # TODO: Implement heater controller task
    raise NotImplementedError("TODO: Person C needs to implement task_heater")


async def task_cooler():
    """
    # TODO: Implement task_cooler.
    
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
    # TODO: Implement cooler controller task
    raise NotImplementedError("TODO: Person C needs to implement task_cooler")


# ==============================================================================
# SECTION D: Humidifier Control & Heartbeat Blinky
# Owner: Ngo Anh Hieu (10423195)
# ==============================================================================

async def task_blinky():
    """
    # TODO: Implement task_blinky.
    
    Required Logic:
    1. Loop forever:
        a. Toggle the onboard LED state (`led_D13.toggle()`).
        b. Asynchronously sleep for `BLINK_INTERVAL_MS`.
    """
    # TODO: Implement blinky heartbeat task
    raise NotImplementedError("TODO: Person D needs to implement task_blinky")


async def task_humidifier():
    """
    # TODO: Implement task_humidifier.
    
    Required Logic:
    1. Loop forever:
        a. Dequeue a reading from `humidifier_queue` (`await humidifier_queue.get()`).
        b. Inspect `humidity_pct`:
           - If humidity < `HUMIDITY_THRESHOLD_PCT`:
             i. Set humidifier LED to GREEN ('#00ff00') and sleep for `HUMIDIFIER_GREEN_MS`.
             ii. Set humidifier LED to YELLOW ('#ffff00') and sleep for `HUMIDIFIER_YELLOW_MS`.
             iii. Set humidifier LED to RED ('#ff0000') and sleep for `HUMIDIFIER_RED_MS`.
             iv. Turn off humidifier LED (set to '#000000').
           - Otherwise:
             Turn off humidifier LED (set to '#000000').
    """
    # TODO: Implement humidifier controller task
    raise NotImplementedError("TODO: Person D needs to implement task_humidifier")


# ==============================================================================
# SECTION A: Startup Self-Test & Event Loop Setup
# Owner: Phan Thanh Hung (10423051)
# ==============================================================================

async def startup_self_test():
    """
    # TODO: Implement startup_self_test.
    
    Required Logic:
    1. Loop through heater_led, cooler_led, and humidifier_led:
        a. Set the LED color to white ('#ffffff').
        b. Asynchronously sleep for 300 ms.
        c. Turn the LED off ('#000000').
    """
    # TODO: Implement self test
    raise NotImplementedError("TODO: Person A needs to implement startup_self_test")


async def setup():
    """
    # TODO: Implement setup sequence.
    
    Required Logic:
    1. Print 'App started' to serial.
    2. Await `startup_self_test()`.
    3. Start all background tasks using `create_task()`:
       - task_blinky()
       - task_read_sensor()
       - task_lcd_display()
       - task_heater()
       - task_cooler()
       - task_humidifier()
    """
    # TODO: Implement tasks startup
    raise NotImplementedError("TODO: Person A needs to implement setup")


async def main():
    """
    # TODO: Implement main scheduler loop.
    
    Required Logic:
    1. Await `setup()`.
    2. Loop forever, asynchronously sleeping for 100 ms in each iteration.
    """
    # TODO: Implement main scheduler loop
    raise NotImplementedError("TODO: Person A needs to implement main")


# TODO: Un-comment this call once Queue and task registration setups are implemented.
# run_loop(main())
