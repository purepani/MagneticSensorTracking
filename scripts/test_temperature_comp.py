from magneticsensortracking import sensors
import board
import numpy as np
import einops as eo
import scipy as sp

from itertools import product

from concurrent.futures import ProcessPoolExecutor
import asyncio
import time

def get_sensor(a, i2c):
    print(f"Starting sensor {hex(a)}")
    s = sensors.Sensors.MLX90393(i2c=i2c, address=a, resolution=0, oversampling=2, filt=4, gain=4, debug=False, temperature_compensation=False)
    print(f"Finished sensor {hex(a)}")
    return s

async def get_sensors(addresses):
    i2c=board.I2C()
    #sensors_tasks = [asyncio.to_thread(get_sensor, a, i2c) for a in addresses]
    sensors = [get_sensor(a, i2c) for a in addresses]
    #sensors = await asyncio.gather(*sensors_tasks)
    return sensors

async def main():
    s = await get_sensors(range(0x0c, 0x1c))
    positions = [[a, b, 0.] for b,a in product(list(np.linspace(-13.5/2,13.5/2, 4, endpoint=True)), list(np.linspace(13.5/2,-13.5/2,4, endpoint=True)))]
    sensor_group = sensors.base.SensorGroup(sensors=s, positions=positions)
    sensor_offset_cal = np.array([sensor.sensor.read_data for sensor in sensor_group.sensors], dtype=np.int32)
    np.savetxt("offset_cal.csv", sensor_offset_cal+0x8000, fmt="%d")

    #while True:
        #for sensor in sensor_group.sensors:
            #print(sensor.get_magnetometer())
            #print(sensor.sensor.temperature)
        #print(50*"-")
        #time.sleep(1)


if __name__=="__main__":
    asyncio.run(main())
