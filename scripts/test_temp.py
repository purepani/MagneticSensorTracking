from magneticsensortracking import sensors, ui, positioning
import board
import uvicorn
import asyncio
from functools import reduce
from itertools import product
import numpy as np
import multiprocessing
from multiprocessing import Pool
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import asyncio

# sensors = sensors.base.SensorGroup(, positions=)


def get_sensor(a, i2c):
    print(f"Starting sensor {hex(a)}")
    while True:
        try:
            s = sensors.Sensors.MLX90393(i2c=i2c, address=a, oversampling=2, filt=4, gain=4)
            break
        except Exception as e:
            print(f"Error connecting to sensor at address {a}: {e}")
            print("Retrying...")
    print(f"Finished sensor {hex(a)}")
    return s

async def get_sensors(addresses):
    i2c=board.I2C()
    sensors_tasks = [asyncio.to_thread(get_sensor, a, i2c) for a in addresses]
    sensors = await asyncio.gather(*sensors_tasks)
    return sensors

sensors = asyncio.get_event_loop().run_until_complete( get_sensors(range(0x0c, 0x1c)))
for s in sensors:
    print(s.get_temperature())
