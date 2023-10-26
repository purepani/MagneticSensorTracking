from quart import Blueprint, render_template, Response, jsonify



videoStreamBp = Blueprint("video_stream", __name__, prefix="picamera")

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

import argparse
import asyncio
import json
import logging
import io
import os
import platform
import ssl

from threading import Condition
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender


class StreamingOutput(VideoStreamTrack, io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()
        super().__init__()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()





picam2 = Picamera2()
video_config = picam2.create_video_configuration({"size": (1280, 720)})
picam2.configure(video_config)
encoder = H264Encoder(1000000)
picam2.encoders = encoder

output = StreamingOutput()
picam2.start_recording(encoder, FileOutput(output))



@videoStreamBp.route("/offer", methods=['POST'])
async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    source = MediaPlayer(output)
    relay = MediaRelay()
    video = relay.subscribe(source.video)


    video_sender = pc.addTrack(video)

    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}



pcs = set()

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()
