from quart import Blueprint, render_template, Response, jsonify, request
from quart.utils import run_sync
import socketio

from magneticsensortracking import sensors
import numpy as np
import einops as eo
import scipy as sp

import argparse
import asyncio
import json
import logging
import io
import os
import platform
import ssl
from collections import deque

from concurrent.futures import ProcessPoolExecutor


class AsyncCircularBuffer:
    def __init__(self, size):
        self.size = size
        self.buffer = deque(maxlen=size)
        self.lock = asyncio.Lock()
        self.not_empty = asyncio.Condition(self.lock)

    async def add(self, item):
        async with self.lock:
            self.buffer.append(item)
            if len(self.buffer) == 1:
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


pool = ProcessPoolExecutor()


class SensorRouting(socketio.AsyncNamespace):
    def __init__(self, sensor_group: sensors.base.SensorGroup, maxlen, *args, **kwargs):
        self.sensor_group = sensor_group
        self.magnet_shape = np.array([25.4 * 3 / 16, 25.4 * 2 / 16])
        self.magnet_magnetization = np.array([1210])
        self.sensor_vals = AsyncCircularBuffer(maxlen)
        self.tasks = []
        self.clients = 0
        # self.tasks.append(asyncio.create_task(self.send_sensor_vals()))
        # self.tasks.append(asyncio.create_task(self.send_predicted_vals()))
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

    async def on_sendMagnet(self, sid, radius, height, magnetism):
        self.magnet_shape = np.array([radius, height])
        self.magnet_magnetization = np.array([magnetism])

    async def send_sensor_vals(self):
        try:
            while True:
                pos, mag = await self.get_sensor_vals()
                data = {"data": [{"pos": p, "mag": m} for p, m in zip(pos, mag)]}
                await self.emit("sensors", data)
        except asyncio.CancelledError:
            print("Sending Sensor Values task cancelled")

    async def send_predicted_vals(self):
        try:
            while True:
                x0 = np.array([0, 0, 30, 0, 0, 1])
                M0 = self.magnet_magnetization
                shape = self.magnet_shape
                queue_vals = await self.sensor_vals.clear_and_retrieve()
                vals = np.asarray(queue_vals)
                mags, pos = np.average(vals, axis=0)
                loop = asyncio.get_running_loop()
                predicted, _ = await asyncio.gather(
                    loop.run_in_executor(pool, minimize, x0, (mags, pos, M0, shape)),
                    asyncio.sleep(0.5),
                )
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
        mags, pos = await asyncio.gather(mags_task, pos_task)  # , asyncio.sleep(0.1))
        await self.sensor_vals.add((mags, pos))
        # await asyncio.sleep(0.1)
        return (pos, mags)


def B_dipole(position, rotation, M0, shape):
    R = np.sqrt(np.sum(position**2, axis=1))
    B = (M0 * (shape[0]) ** 2 * shape[1] / (16)) * (
        (
            3
            * position
            / R[:, np.newaxis] ** 5
            * (eo.einsum(position, rotation, "sensor dim,  dim -> sensor"))[
                :, np.newaxis
            ]
        )
        - rotation[np.newaxis, :] / (R[:, np.newaxis] ** 3)
    )
    return B


def getField_dipole(x, positions, M0, shape):
    # magnetization=x[5]
    # magnetization=1210
    position = x[:3]
    axis = x[3:]
    # axis=np.array([0,0,1])
    # phi = x[3]
    # theta = x[4]
    # axis = np.array([np.sin(theta)*np.cos(phi), np.sin(theta)*np.sin(phi), np.cos(theta)])
    return B_dipole(positions - position, axis, M0, shape)


def getField_dipole_fixed(x, positions, M0, shape):
    # magnetization=x[5]
    # magnetization=1210
    position = x[:3]
    axis = x[3:]
    # axis = np.array([0.0, 0.0, 1.0])
    # phi = x[3]
    # theta = x[4]
    # axis = np.array([np.sin(theta)*np.cos(phi), np.sin(theta)*np.sin(phi), np.cos(theta)])
    return B_dipole(positions - position, axis, M0, shape)


def cost_dipole(x, B, positions, M0, shape):
    diff = getField_dipole(x, positions, M0, shape) - B
    return np.sum((diff) ** 2)


def minimize(x0, args):
    print("Starting mimimization")
    # x0 = [x, y, z, th_x, th_y, th_z]
    cons = [{"type": "eq", "fun": lambda x: x[3] ** 2 + x[4] ** 2 + x[5] ** 2 - 1}]
    bounds = [(-100, 100), (-100, 100), (0, 100), (-1, 1), (-1, 1), (-1, 1)]
    res = sp.optimize.minimize(
        fun=cost_dipole, x0=x0, args=args, tol=1e-100, constraints=cons, bounds=bounds
    ).x  # , options={'maxiter': 1000}).x
    print(f"Finished mimimization with shape {args[3]} at {res}")
    return res
