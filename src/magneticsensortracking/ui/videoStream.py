from quart import Blueprint, redirect, render_template, Response, jsonify, request



import picamera2
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, MJPEGEncoder, Encoder
from picamera2.outputs import FileOutput
from time import time

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






videoStreamBp = Blueprint("video_stream", __name__, url_prefix="/picamera")

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

#defines the function that generates our frames
def genFrames():
    #buffer = StreamingOutput()
    with picamera2.Picamera2() as camera:
        output = StreamingOutput()
        camera.configure(camera.create_video_configuration(main={"size": (640, 480)}))
        output = StreamingOutput()
        camera.start_recording(MJPEGEncoder(), FileOutput(output))
        while True:
            with output.condition:
                output.condition.wait()
                frame = output.frame
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@videoStreamBp.route('/video.mp4')
def video_feed():
    return redirect(f"http://0.0.0.0:8000/video.mp4?{int(time())}")

@videoStreamBp.route('/video.m3u')
def video_feed_m3u8():
    return redirect("http://0.0.0.0:8000/video.m3u8")
