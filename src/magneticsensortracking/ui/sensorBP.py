import argparse
import asyncio
import io
import json
import logging
import os
import platform
import ssl
from collections import deque
from concurrent.futures import ProcessPoolExecutor

import einops as eo
import numpy as np
import scipy as sp
import socketio
from quart import Blueprint, Response, jsonify, render_template, request
from quart.utils import run_sync

from magneticsensortracking import sensors
from magneticsensortracking.optimization.dipole import minimize

from pathlib import Path

from datetime import datetime

class AsyncCircularBuffer:
    def __init__(self, size):
        self.size = size
        self.buffer = deque(maxlen=size)
        self.lock = asyncio.Lock()
        self.not_empty = asyncio.Condition(self.lock)

    async def add(self, item):
        async with self.lock:
            self.buffer.append(item)
            if len(self.buffer) >= 1:
                self.not_empty.notify_all()

    async def remove(self):
        async with self.lock:
            if len(self.buffer) == 0:
                raise Exception("Buffer is empty")
            return self.buffer.popleft()

    async def clear_and_retrieve(self):
        async with self.not_empty:
            while len(self.buffer) == 0:
                await self.not_empty.wait()
            items = list(self.buffer)
            self.buffer.clear()
            return items

class AsyncBufferAndWriter:
    def __init__(self, size, log_path):
        self.buffer = AsyncCircularBuffer(size)
        self.path = Path(log_path)
        self.path.mkdir()

    async def addData(self, mags, pos, temp):
        await self.buffer.add([np.asarray(mags), np.asarray(pos), np.asarray(temp)])

    async def removeData(self):
        await self.buffer.remove()

    async def getAndLogData(self):
        vals = await self.buffer.clear_and_retrieve()
        mags_and_pos = np.asarray([sample[:2] for sample in vals])
        mags = mags_and_pos[:, 0]
        pos = mags_and_pos[:, 1]
        temp = np.asarray([sample[2] for sample in vals])
        time = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        print(time)
        data_to_save = {f'mags': mags,f'pos': pos, f'temp': temp}
        with open(self.path / f'{time}.npz', 'wb') as f:
            np.savez(f, **data_to_save)
        return vals

    async def setLoggingPath(self, log_path):
        self.path = Path(log_path)
        self.path.mkdir()

pool = ProcessPoolExecutor()


class SensorRouting(socketio.AsyncNamespace):
    def __init__(self, sensor_group: sensors.base.SensorGroup, maxlen, *args, **kwargs):
        self.sensor_group = sensor_group
        self.magnet_shape = np.array([25.4 * 3 / 16, 25.4 * 2 / 16])
        self.magnet_magnetization = np.array([1480])
        time = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        self.sensor_vals = AsyncBufferAndWriter(maxlen, str(f'/home/raspberrypi/logs/{time}'))
        self.current_prediction = np.zeros((6,))
        self.shift = np.array([0, 0, 0])
        self.tasks = []
        self.clients = 0
        self.tasks.append(asyncio.create_task(self.send_sensor_vals()))
        self.tasks.append(asyncio.create_task(self.send_predicted_vals()))
        super().__init__(*args, **kwargs)

    async def on_connect(self, sid, enivron):
        self.clients += 1
        print(f"Client joined. Total current clients: {self.clients}")
        if len(self.tasks) == 0:
            self.tasks.append(asyncio.create_task(self.send_sensor_vals()))
            self.tasks.append(asyncio.create_task(self.send_predicted_vals()))

    async def on_disconnect(self, sid):
        self.clients -= 1
        print(f"Client left. Total current clients: {self.clients}")
        if self.clients == 0:
            for task in self.tasks:
                task.cancel()
            self.tasks.clear()

    async def on_sendMagnet(
        self, sid, radius, radius_unit, height, height_unit, magnetism, magnetism_unit
    ):
        length_conversion = {
            "mm": 1,
            "inch": 25.4,
            "inch/16": 25.4 / 16,
            "inch/32": 25.4 / 32,
        }
        magnetism_conversion = {"mT": 1}
        convert = lambda conv, val, val_unit: conv[val_unit] * val
        radius_c = convert(length_conversion, radius, radius_unit)
        height_c = convert(length_conversion, height, height_unit)
        magnetism_c = convert(magnetism_conversion, magnetism, magnetism_unit)
        print(f"Changed radius to {radius_c} mm.(sent {radius} {radius_unit})")
        print(f"Changed height to {height_c} mm.(sent {height} {height_unit})")
        print(f"Changed radius to {magnetism_c} mT.(sent {magnetism} {magnetism_unit})")

        self.magnet_shape = np.array([radius_c, height_c])
        self.magnet_magnetization = np.array([magnetism_c])

    async def send_sensor_vals(self):
        try:
            while True:
                pos, mag, temp = await self.get_sensor_vals()
                data = {
                    "data": [
                        {
                            "pos": p,
                            "mag": m,
                            "temp": t,
                        }
                        for p, m, t in zip(pos, mag, temp)
                    ]
                }
                await self.emit("sensors", data)
        except asyncio.CancelledError:
            print("Sending Sensor Values task cancelled")

    async def send_predicted_vals(self):
        try:
            while True:
                x0 = np.array([0, 0, 30, 0, 0, 1])
                M0 = self.magnet_magnetization
                shape = self.magnet_shape
                queue_vals = await self.sensor_vals.getAndLogData()
                vals = np.asarray([sample[:2] for sample in queue_vals])
                mags, pos, = np.average(vals, axis=0)
                loop = asyncio.get_running_loop()
                calc_predicted, _ = await asyncio.gather(
                    loop.run_in_executor(pool, minimize, x0, mags, pos, M0, shape),
                    asyncio.sleep(0.5),
                    return_exceptions=True
                )
                for val in calc_predicted:
                    if val is Exception:
                        raise val
                self.current_prediction = calc_predicted
                predicted = calc_predicted - np.pad(self.shift, (0, 3))
                data = {
                    "pos": {"x": predicted[0], "y": predicted[1], "z": predicted[2]},
                    "rot": {"x": predicted[3], "y": predicted[4], "z": predicted[5]},
                }
                await self.emit("predicted", data)
        except asyncio.CancelledError:
            print("Sending Predicted Values Cancelled")

    async def get_sensor_vals(self):
        mags_task = asyncio.to_thread(self.sensor_group.get_magnetometer)
        pos_task = asyncio.to_thread(self.sensor_group.get_positions)

        mags_and_temp, pos = await asyncio.gather(
            mags_task, pos_task, return_exceptions=True
        )  # , asyncio.sleep(0.1))
        for m in mags_and_temp:
            if m is Exception:
                raise m
        temp = [m[3] for m in mags_and_temp]
        mags = [m[:3] for m in mags_and_temp]
        await self.sensor_vals.addData(mags, pos, temp)
        await asyncio.sleep(0.1)
        return (pos, mags, temp)

    async def on_zero(self, sid):
        self.shift = self.current_prediction[:3]
        print(f"Current shift set to {self.shift}")

    async def on_setSensorSetting(self, sid, setting, setting_val):
        sensors = self.sensor_group.sensors
        print(setting, setting_val)
        print(dir(sensors[0]))
        valid_attrs = {
            "filter",
            "gain",
            "oversampling",
            "resolution_x",
            "resolution_y",
            "resolution_z",
        }
        if setting in valid_attrs:
            if setting == "filter":
                for s in sensors:
                    s.filter = setting_val
            elif setting == "gain":
                for s in sensors:
                    s.gain = setting_val
            elif setting == "oversampling":
                for s in sensors:
                    s.oversampling = setting_val
            elif setting == "resolution_x":
                for s in sensors:
                    s.resolution_x = setting_val
            elif setting == "resolution_y":
                for s in sensors:
                    s.resolution_y = setting_val
            elif setting == "resolution_z":
                for s in sensors:
                    s.resolution_z = setting_val

    async def on_setTemperatureCompensation(self, sid, tempCompEnabled):
        try:
            for i, sensor in enumerate(self.sensor_group.sensors):
                print(f"sensor {i} temp comp")
                sensor.temperature_compensation = tempCompEnabled
            await self.emit("sendTemperatureCompensation", tempCompEnabled)
        except Exception as e:
            await self.emit("sendTemperatureCompensation", not tempCompEnabled)
            raise e
    async def on_reset_logging(self, sid):
        time = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        path = str(f'/home/raspberrypi/logs/{time}')
        await self.sensor_vals.setLoggingPath(path)
