

import sys

sys.path.append('../')
import gi
import configparser

gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst
from ctypes import *
import time
import sys
import math
import platform
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.FPS import PERF_DATA
import numpy as np
import pyds
import cv2
from configs import configs
from services.deepstream import ServiceDeepStream


def main(args):
    # Check input arguments
    global pipeline, loop
    perf_data = PERF_DATA(configs.MAX_NUM_SOURCES)
    Gst.init(None)
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()
    loop = GLib.MainLoop()

    deepstream = ServiceDeepStream(pipeline,loop, sources=[(1,"file:///media/ngoc-thanhluu/data/thanhlnbka/Projects/behaviorhuman/videos/video_inputdemo/intrusion.mp4")])
    deepstream.create_pipeline()
    bus = deepstream.pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, deepstream.loop)



    # tiler_sink_pad = deepstream.tiler.get_static_pad("sink")
    # if not tiler_sink_pad:
    #     sys.stderr.write(" Unable to get src pad \n")
    # else:
    #     tiler_sink_pad.add_probe(Gst.PadProbeType.BUFFER, tiler_sink_pad_buffer_probe, 0)
    # #     # perf callback function to print fps every 5 sec
    # #     GLib.timeout_add(5000, perf_data.perf_print_callback)

    # List the sources
    print("Now playing...")
    for i, source in enumerate(args[:-1]):
        if i != 0:
            print(i, ": ", source)

    print("Starting pipeline \n")
    # start play back and listed to events
    deepstream.pipeline.set_state(Gst.State.PLAYING)    
    data = [(2+i,"file:///media/ngoc-thanhluu/data/thanhlnbka/Projects/behaviorhuman/videos/video_inputdemo/intrusion.mp4") for i in range(7)]
    cam_id = [1,3,5,8]

    GLib.timeout_add_seconds(5, deepstream.add_source,data)
    GLib.timeout_add_seconds(8, deepstream.delete_source,cam_id)
    try:
        deepstream.loop.run()
    except:
        pass
    # cleanup
    print("Exiting app\n")
    deepstream.pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    sys.exit(main(sys.argv))