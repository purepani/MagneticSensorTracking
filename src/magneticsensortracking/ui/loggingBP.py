from quart import Blueprint, render_template, Response, jsonify, request
import socketio

from magneticsensortracking import positioning, sensors

import argparse
import asyncio
import json
import logging
import io
import os
import platform
import ssl


class Logging(socketio.AsyncNamespace):
    def __init__(
        self,
        sensor_group: sensors.base.SensorGroup,
        printer: positioning.base.Path,
        samples: int = 10,
        *args,
        **kwargs,
    ):
        self.measurement_index = 0
        self.printer = printer
        self.sensor_group = sensor_group
        self.samples = samples
        self.save_path = "/home/raspberrypi/measurements"
        self.current_folder = "";
        self.measuring = False
        super().__init__(*args, **kwargs)

    async def on_start_measurement(self, sid):
        self.measurement_index = 0
        path = f"{self.save_path}/{self.current_folder}"
        if not os.path.exists(path):
            os.makedirs(path)
            print("Created Path")
        print("Ready For Measurements")
        

    async def on_record_measurement(self, sid):
        self.measuring=True
        print("Recording Measurement")
        pos = self.printer.getPos()
        mags = [await self.get_sensor_vals() for _ in range(self.samples)]
        file_path = f"{self.save_path}/{self.current_folder}/{self.measurement_index}.data"
        with open(file_path, "w+") as f:
            print(f"Opened {file_path}") 
            f.write("Position\n")
            f.write(f"{','.join(map(str, pos))}\n")
            f.write("Magentizations\n")
            #f.writelines(map(lambda l: ', '.join(map(lambda p: str(tuple(p)), l)), mags))
            create_sens_string = lambda x: f"({','.join(map(str, x))})"
            create_line = lambda l: ', '.join(map(create_sens_string, l))+"\n"
            list(map(f.write, map(create_line, mags)))

        self.measurement_index += 1
        self.measuring=False
        print("Finished Recording")
        await self.emit("finished_measurement")

    async def on_get_settings(self, sid):
        await self.emit("settings", 
                            {
                            "samples": self.samples,
                            "folder": f"{self.save_path}/{self.current_folder}"
                            }
                        )


    async def on_set_settings(self, sid, folder, samples):
        self.current_folder = folder
        self.samples = int(samples)
        await self.emit("settings", 
                            {
                            "samples": self.samples,
                            "folder": f"{self.save_path}/{self.current_folder}"
                            }
                        )

    async def get_sensor_vals(self):
        mags_task = asyncio.to_thread(self.sensor_group.get_magnetometer)
        pos_task = asyncio.to_thread(self.sensor_group.get_positions)
        mags, pos = await asyncio.gather(mags_task, pos_task)  # , asyncio.sleep(0.1))
        # await asyncio.sleep(0.1)
        return (pos, mags)
