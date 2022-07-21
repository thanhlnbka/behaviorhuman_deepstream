

from calendar import c
import sys

from matplotlib import image

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


def tiler_sink_pad_buffer_probe(pad, info, u_data):
    global socket
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break
        l_obj = frame_meta.obj_meta_list
        n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
        frame_copy = np.array(n_frame, copy=True, order='C')
        frame_copy = cv2.cvtColor(frame_copy, cv2.COLOR_RGBA2BGRA)

        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            # frame_copy, box = draw_bounding_boxes(frame_copy, obj_meta, obj_meta.confidence)
            l_user_meta = obj_meta.obj_user_meta_list
            try:
                l_obj = l_obj.next
            except StopIteration:
                break
        # message = {"frame_shape": frame_copy.shape, "cam_id":frame_meta.pad_index}
        ## RULE BEHAVIOR AND SEND FRAME, MESSEAGE HERE
        # result, image = cv2.imencode('.jpg', frame_copy, encode_param)
        # frame = image.tobytes()

        # frame = base64.encodebytes(frame).decode("utf-8")
        # json_data = {"cam_id":frame_meta.pad_index, "img_base64":frame}
        # sio.emit('send', json_data)
        
        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK


def draw_bounding_boxes(image, obj_meta, confidence):

    confidence = '{0:.2f}'.format(confidence)
    rect_params = obj_meta.rect_params
    top = int(rect_params.top)
    left = int(rect_params.left)
    width = int(rect_params.width)
    height = int(rect_params.height)
    obj_name = configs.pgie_classes_str[obj_meta.class_id]
    image = cv2.rectangle(image, (left, top), (left + width, top + height), (2,55,222), 2, cv2.LINE_4)
    box = [left, top, left+width, top+height, float(confidence)]
    # print(image.shape)
    return image, box




def main(process_id):
    # Check input arguments
    global pipeline, loop
    #Thread(target=send_socket).start()
    perf_data = PERF_DATA(configs.MAX_NUM_SOURCES)
    Gst.init(None)
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()
    loop = GLib.MainLoop()
    # mystreams = [[(i,f"rtsp://192.168.6.119:8554/mystream{i}") for i in range(1,7)],[(i,f"rtsp://192.168.6.119:8554/mystream{i}") for i in range(10,15)],[(i,f"rtsp://192.168.6.119:8554/mystream{i}") for i in range(20,25)]]
    mystreams = [[(1,"rtsp://192.168.6.113:8554/mystream79"),((2,"rtsp://192.168.6.113:8554/mystream80"))]]
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
        tiler_sink_pad.add_probe(Gst.PadProbeType.BUFFER, tiler_sink_pad_buffer_probe, 0)
    #     # perf callback function to print fps every 5 sec
    #     GLib.timeout_add(5000, perf_data.perf_print_callback)
    
    

    print("Starting pipeline \n")
    # start play back and listed to events
    deepstream.pipeline.set_state(Gst.State.PLAYING)    
    # data = [(2,"rtsp://192.168.6.113:8554/mystream2")]
    # data = [(2,"rtsp://admin:Comit123@192.168.6.108:554")]
    # data = [(i+1, "rtsp://192.168.6.120:2468/test") for i in range(2)]
    # data = [(2,'rtsp://admin:Billgo123!@192.168.6.70:554/profile1/media.smp'),(3,'rtsp://admin:Comit123@192.168.6.108:554')]
    # cam_id = [2,7,8]


    # GLib.timeout_add_seconds(5, deepstream.add_source,data)
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