
import sys

from matplotlib import image
from psycopg2 import Timestamp

sys.path.append('../')

from logics.behavior import HumanBehavior
from logics.timestamp import TimeStampID

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
import json 
import socketio
import base64
from threading import Thread

# global sio 


# def send_socket():
#     global sio
#     sio = socketio.Client(engineio_logger=False)
#     sio.connect('http://0.0.0.0:5000')
#     sio.wait()



encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]

def nvanalytics_src_pad_buffer_probe(pad,info,u_data):
    frame_number=0
    num_rects=0
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    # Retrieve batch metadata from the gst_buffer
    # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
    # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list

    while l_frame:
        try:
            # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
            # The casting is done by pyds.NvDsFrameMeta.cast()
            # The casting also keeps ownership of the underlying memory
            # in the C code, so the Python garbage collector will leave
            # it alone.
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        frame_number=frame_meta.frame_num
        l_obj=frame_meta.obj_meta_list
        num_rects = frame_meta.num_obj_meta
        print("#"*50)
        while l_obj:
            try: 
                # Note that l_obj.data needs a cast to pyds.NvDsObjectMeta
                # The casting is done by pyds.NvDsObjectMeta.cast()
                obj_meta=pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            l_user_meta = obj_meta.obj_user_meta_list
            # Extract object level meta data from NvDsAnalyticsObjInfo
            while l_user_meta:
                try:
                    user_meta = pyds.NvDsUserMeta.cast(l_user_meta.data)
                    if user_meta.base_meta.meta_type == pyds.nvds_get_user_meta_type("NVIDIA.DSANALYTICSOBJ.USER_META"):             
                        user_meta_data = pyds.NvDsAnalyticsObjInfo.cast(user_meta.user_meta_data)
                        if user_meta_data.roiStatus: 
                            print("Object {0} roi status: {1}".format(obj_meta.object_id, user_meta_data.roiStatus))
                            rect_params = obj_meta.rect_params
                            top = int(rect_params.top)
                            left = int(rect_params.left)
                            width = int(rect_params.width)
                            height = int(rect_params.height)
                            box = [left, top, left+width, top+height, float(obj_meta.confidence)]
                            print(box)
                            
                            

                except StopIteration:
                    break

                try:
                    l_user_meta = l_user_meta.next
                except StopIteration:
                    break
            try: 
                l_obj=l_obj.next
            except StopIteration:
                break
        # XU LY LOGIC => SEND INFO CLIENT
    
        
        try:
            l_frame=l_frame.next
        except StopIteration:
            break
        print("#"*50)

    return Gst.PadProbeReturn.OK





def main(process_id):
    # Check input arguments
    global pipeline, loop, timestamp, behavior 
    #Thread(target=send_socket).start()
    perf_data = PERF_DATA(configs.MAX_NUM_SOURCES)
    Gst.init(None)
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()
    loop = GLib.MainLoop()
    
    # mystreams = [[(i,f"rtsp://192.168.6.119:8554/mystream{i}") for i in range(1,7)],[(i,f"rtsp://192.168.6.119:8554/mystream{i}") for i in range(10,15)],[(i,f"rtsp://192.168.6.119:8554/mystream{i}") for i in range(20,25)]]
    mystreams = [[(1,"rtsp://192.168.6.113:8554/mystream79"),((2,"rtsp://192.168.6.113:8554/mystream80"))]]
    # timestamps = [TimeStampID(cam_id=i+1) for i in range(2)]
    # behavior = HumanBehavior(timestamps)
    # mystreams = [[(1,"rtsp://admin:Comit123@192.168.6.108:554")]]
    deepstream = ServiceDeepStream(pipeline,loop, sources=mystreams[process_id])
    deepstream.create_pipeline()
    bus = deepstream.pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, deepstream.loop)



    tiler_sink_pad = deepstream.tiler.get_static_pad("sink")
    if not tiler_sink_pad:
        sys.stderr.write(" Unable to get src pad \n")
    else:
        tiler_sink_pad.add_probe(Gst.PadProbeType.BUFFER, nvanalytics_src_pad_buffer_probe, 0)
    #     # perf callback function to print fps every 5 sec
    #     GLib.timeout_add(5000, perf_data.perf_print_callback)
    
    

    print("Starting pipeline \n")
    # start play back and listed to events
    deepstream.pipeline.set_state(Gst.State.PLAYING)    
    data = [(i,f"rtsp://192.168.6.113:8554/mystream{i}") for i in range(4,8)]

    GLib.timeout_add_seconds(5, deepstream.add_source,data)
    # GLib.timeout_add_seconds(8, deepstream.delete_source,cam_id)
    GLib.timeout_add_seconds(1, deepstream.update_polygon)
    try:
        deepstream.loop.run()
    except:
        pass
    
    # cleanup
    print("Exiting app\n")
    deepstream.pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    from multiprocessing import Process
    for i in range(1):
        Process(target=main, args=(i,),).start()