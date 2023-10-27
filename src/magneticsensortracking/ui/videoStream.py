from quart import Blueprint, render_template, Response, jsonify, request




from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, MJPEGEncoder, Encoder
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
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender

class OverwrittenCamera(MediaStreamTrack):
    kind = "video"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # don't forget this!
        self.cam = Picamera2()
        self.cam.configure(self.cam.create_preview_configuration())
        self.cam.start()

    async def recv(self):

        img = self.cam.capture_array()

        # Calculating the representation time in term of microseconds
        pts = time.time() * 1000000

        # rebuild a VideoFrame, preserving timing information
        new_frame = VideoFrame.from_ndarray(img, format='rgba')
        new_frame.pts = int(pts)
        new_frame.time_base = Fraction(1,1000000)
        return new_frame

class CameraBlueprint(Blueprint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = MediaPlayer('/dev/video0', format="v4l2", options={"video_size": "640x480"})
        self.relay = MediaRelay()
        self.video = self.relay.subscribe(self.source.video)



videoStreamBp = CameraBlueprint("video_stream", __name__, url_prefix="/picamera")


def force_codec(pc, sender, forced_codec):
    kind = forced_codec.split("/")[0]
    codecs = RTCRtpSender.getCapabilities(kind).codecs
    transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
    transceiver.setCodecPreferences(
        [codec for codec in codecs if codec.mimeType == forced_codec]
    )

@videoStreamBp.route("/offer", methods=['POST'])
async def offer():
    params = await request.json
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)
            print("Failed")

    #source = MediaPlayer(videoStreamBp.output, decode=False)
    video = videoStreamBp.video


    video_sender = pc.addTrack(video)
    #force_codec(pc, video_sender, 'video/h264')

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
