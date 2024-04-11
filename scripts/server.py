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
    s = sensors.Sensors.MLX90393(i2c=i2c, address=a, oversampling=2, filt=4, gain=4, resolution=0, debug=False)
    print(f"Finished sensor {hex(a)}")
    return s

async def get_sensors(addresses):
    i2c=board.I2C()
    #sensors_tasks = [asyncio.to_thread(get_sensor, a, i2c) for a in addresses]
    #sensors = await asyncio.gather(*sensors_tasks)
    sensors = [get_sensor(a, i2c) for a in addresses]
    return sensors

def create_app(sensors):
    #sensors = [
        #sensors.Sensors.VIRTUAL() for a in range(16, 32)
    #]

    #positions = [[0.0, 0.0, 0.0], [25.0, 0.0, 0.0], [0.0, 25.0, 0.0], [25.0, 25.0, 0.0]]
    #app_factory.setFakePrinter()
    s = sensors
    positions = [[a, b, 0.] for b,a in product(list(np.linspace(-13.5/2,13.5/2, 4, endpoint=True)), list(np.linspace(13.5/2,-13.5/2,4, endpoint=True)))]
    for a, p in zip(range(0x0c, 0x1c), positions):
            print(hex(a), p)
    #printer = positioning.devices.PRUSA(
    #    "/dev/serial/by-id/usb-Prusa_Research__prusa3d.com__Original_Prusa_i3_MK2_CZPX1017X003XC14071-if00",
    #    115200,
    #)
    printer = positioning.devices.VIRTUAL()
    app_factory = ui.AppFactory()
    app_factory = reduce(
        lambda x, y: x.addSensor(*y), zip(s, positions), app_factory
    )
    app_factory.setPrinter(printer)
    return app_factory.create_app()

async def main():
    sensors = await get_sensors(range(0x0c, 0x1c))
    offsets = np.loadtxt("offset_cal.csv", dtype=np.uint16)
    for i, sensor in enumerate(sensors):
        sensor.sensor.write_reg(0x04, offsets[i, 0])
        sensor.sensor.write_reg(0x05, offsets[i, 1])
        sensor.sensor.write_reg(0x06, offsets[i, 2])
    app = create_app(sensors)
    #uvicorn.rnn("server:create_app", port=5000, host="127.0.0.1")
    config = uvicorn.Config(app, port=5000, host="127.0.0.1")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
