
import sys 
import gi 
gi.require_version("Gst","1.0")
from gi.repository import GLib, Gst
from common.is_aarch_64 import *
from configs import configs
import configparser
import math
import pyds

class ServiceDeepStream:
    def __init__(self, pipeline, loop, sources):
        self.pipeline = pipeline
        self.loop = loop

        self.streammux = None 
        self.tracker = None 
        self.pgie = None 
        self.nvvidconv = None 
        self.nvvidconv1 = None
        self.filter = None 
        self.transform = None
        self.nvosd = None 
        self.sink = None

        self.g_source = {}
        self.g_source_bin = {}
        self.g_num_source = 0
        
        self.sources = sources
        self.init_stream()

    
    def init_stream(self):
        for source in self.sources:
            print("Creating source_bin ", source[0], " \n ")
            source_bin = self.create_uridecode_bin(source[0], source[1])
            if not source_bin:
                sys.stderr.write("Unable to create source bin \n")

            self.pipeline.add(source_bin)
            self.g_source_bin[source[0]] = source_bin
            self.g_source[source[0]] = True
            self.g_num_source += 1
        

    def add_source(self,data):
        for d in data:
            cam_id = d[0]
            uri = d[1]
            self.g_source[cam_id] = True 
            print("Calling Start cam_id: %d " % cam_id)
            source_bin = self.create_uridecode_bin(cam_id,uri)
            if (not source_bin):
                sys.stderr.write("Failed to create source bin. Exiting.")
                exit(1)
            
            self.g_source_bin[cam_id] = source_bin
            self.pipeline.add(source_bin)

            #set state of source bin playing 

            state_return = self.g_source_bin[cam_id].set_state(Gst.State.PLAYING)
            
            if state_return == Gst.StateChangeReturn.SUCCESS:
                print("STATE CHANGE SUCCESS\n")

            elif state_return == Gst.StateChangeReturn.FAILURE:
                print("STATE CHANGE FAILURE\n")
            
            elif state_return == Gst.StateChangeReturn.ASYNC:
                state_return = self.g_source_bin[cam_id].get_state(Gst.CLOCK_TIME_NONE)

            elif state_return == Gst.StateChangeReturn.NO_PREROLL:
                print("STATE CHANGE NO PREROLL\n")
            self.g_num_source += 1

        return True 

    def delete_source(self, cam_ids):
        for cam_id in cam_ids:
            print("Calling Stop cam_id: %d"%cam_id)
            self.g_source[cam_id] = False
            self.stop_source(cam_id) 
            if (self.g_num_source == 0):
                self.loop.quit()
                print("All sources stopped quitting")
                return False
        return True 
        

    def stop_source(self, cam_id):
        #Attempt to change status of source to be released 
        state_return = self.g_source_bin[cam_id].set_state(Gst.State.NULL)
        if state_return == Gst.StateChangeReturn.SUCCESS:
            print("STATE CHANGE SUCCESS\n")
            pad_name = "sink_%u" % cam_id
            print(pad_name)
            #Retrieve sink pad to be released
            sinkpad = self.streammux.get_static_pad(pad_name)
            #Send flush stop event to the sink pad, then release from the streammux
            sinkpad.send_event(Gst.Event.new_flush_stop(False))
            self.streammux.release_request_pad(sinkpad)
            print("STATE CHANGE SUCCESS\n")
            #Remove the source bin from the pipeline
            self.pipeline.remove(self.g_source_bin[cam_id])
            self.g_num_source -= 1

        elif state_return == Gst.StateChangeReturn.FAILURE:
            print("STATE CHANGE FAILURE\n")
        
        elif state_return == Gst.StateChangeReturn.ASYNC:
            state_return = self.g_source_bin[cam_id].get_state(Gst.CLOCK_TIME_NONE)
            pad_name = "sink_%u" % cam_id
            print(pad_name)
            sinkpad = self.streammux.get_static_pad(pad_name)
            sinkpad.send_event(Gst.Event.new_flush_stop(False))
            self.streammux.release_request_pad(sinkpad)
            print("STATE CHANGE ASYNC\n")
            self.pipeline.remove(self.g_source_bin[cam_id])
            self.g_num_source -= 1

    def cb_newpad(self,decodebin,pad,data):
        print("In cb_newpad\n")
        caps=pad.get_current_caps()
        gststruct=caps.get_structure(0)
        gstname=gststruct.get_name()

        print("gstname=",gstname)
        if(gstname.find("video")!=-1):
            source_id = data
            pad_name = "sink_%u" % source_id
            print(pad_name)
            #Get a sink pad from the streammux, link to decodebin
            sinkpad = self.streammux.get_request_pad(pad_name)
            if pad.link(sinkpad) == Gst.PadLinkReturn.OK:
                print("Decodebin linked to pipeline")
            else:
                sys.stderr.write("Failed to link decodebin to pipeline\n")

    def decodebin_child_added(self,child_proxy,Object,name,user_data):
        print("Decodebin child added:", name, "\n")
        if(name.find("decodebin") != -1):
            Object.connect("child-added",self.decodebin_child_added,user_data)   
        if(name.find("nvv4l2decoder") != -1):
            if (is_aarch64()):
                Object.set_property("enable-max-performance", True)
                Object.set_property("drop-frame-interval", 0)
                Object.set_property("num-extra-surfaces", 0)
            else:
                Object.set_property("gpu_id", configs.GPU_ID)

    

    def create_uridecode_bin(self,cam_id,filename):
        print("Creating uridecodebin for [%s]" % filename)
        bin_name="source-bin-%02d" % cam_id
        print(bin_name)
        bin=Gst.ElementFactory.make("uridecodebin", bin_name)
        if not bin:
            sys.stderr.write(" Unable to create uri decode bin \n")
        bin.set_property("uri",filename)
        bin.connect("pad-added",self.cb_newpad,cam_id)
        bin.connect("child-added",self.decodebin_child_added,cam_id)

        self.g_source[cam_id] = True

        return bin

    def make_elements(self):
        self.streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
        self.pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
        self.tracker = Gst.ElementFactory.make("nvtracker", "tracker")
        self.nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
        self.nvvidconv1 = Gst.ElementFactory.make("nvvideoconvert", "convertor1")
        self.filter = Gst.ElementFactory.make("capsfilter", "filter")
        self.tiler = Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
        self.nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
        self.nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
        if (is_aarch64()):
            self.transform = Gst.ElementFactory.make("nvegltransform", "nvegl-transform")
        self.sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")


        
    def set_property_elements(self):
        # streamux 
        self.streammux.set_property('batch-size', configs.MAX_NUM_SOURCES)
        self.streammux.set_property('batched-push-timeout', 40)
        self.streammux.set_property("gpu_id", configs.GPU_ID)
        self.streammux.set_property('live-source',1)
        self.streammux.set_property('width', 640)
        self.streammux.set_property('height', 640)

        #pgie 
        self.pgie.set_property('config-file-path', configs.PGIE_CONFIG_FILE)
        self.pgie.set_property("batch-size", configs.MAX_NUM_SOURCES)
        self.pgie.set_property("gpu-id",configs.GPU_ID)


        #tracker
        cfg_tracker = configparser.ConfigParser()
        cfg_tracker.read(configs.TRACKER_CONFIG_FILE)
        cfg_tracker.sections()
        for key in cfg_tracker['tracker']:
            if key == 'tracker-width' :
                tracker_width = cfg_tracker.getint('tracker', key)
                self.tracker.set_property('tracker-width', tracker_width)
            if key == 'tracker-height' :
                tracker_height = cfg_tracker.getint('tracker', key)
                self.tracker.set_property('tracker-height', tracker_height)
            if key == 'gpu-id' :
                tracker_gpu_id = cfg_tracker.getint('tracker', key)
                self.tracker.set_property('gpu_id', tracker_gpu_id)
            if key == 'll-lib-file' :
                tracker_ll_lib_file = cfg_tracker.get('tracker', key)
                self.tracker.set_property('ll-lib-file', tracker_ll_lib_file)
            if key == 'll-config-file' :
                tracker_ll_config_file = cfg_tracker.get('tracker', key)
                self.tracker.set_property('ll-config-file', tracker_ll_config_file)
            if key == 'enable-batch-process' :
                tracker_enable_batch_process = cfg_tracker.getint('tracker', key)
                self.tracker.set_property('enable_batch_process', tracker_enable_batch_process)


        #filter 
        caps = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA")
        self.filter.set_property("caps", caps)

        #tiler 
        tiler_rows = int(math.sqrt(configs.MAX_NUM_SOURCES))
        tiler_columns = int(math.ceil((1.0 * configs.MAX_NUM_SOURCES) / tiler_rows))
        self.tiler.set_property("rows", tiler_rows)
        self.tiler.set_property("columns", tiler_columns)
        self.tiler.set_property("width", configs.TILED_OUTPUT_WIDTH)
        self.tiler.set_property("height", configs.TILED_OUTPUT_HEIGHT)
        self.tiler.set_property("gpu_id",configs.GPU_ID)

        #nvvidconv , nvvidconv1, nvosd
        self.nvvidconv.set_property("gpu_id", configs.GPU_ID)
        self.nvvidconv1.set_property("gpu_id", configs.GPU_ID)
        self.nvosd.set_property("gpu_id", configs.GPU_ID)

        #sink 
        self.sink.set_property("sync", 0)
        self.sink.set_property("qos", 0)

        # is aarch64 
        if not is_aarch64():
            # Use CUDA unified memory in the pipeline so frames
            # can be easily accessed on CPU in Python.
            mem_type = int(pyds.NVBUF_MEM_CUDA_UNIFIED)
            self.streammux.set_property("nvbuf-memory-type", mem_type)
            self.nvvidconv.set_property("nvbuf-memory-type", mem_type)
            self.nvvidconv1.set_property("nvbuf-memory-type", mem_type)
            self.tiler.set_property("nvbuf-memory-type", mem_type)

    def create_pipeline(self):
        self.make_elements()
        self.set_property_elements()

        print("Adding elements to Pipeline")
        self.pipeline.add(self.streammux)
        self.pipeline.add(self.pgie)
        self.pipeline.add(self.tracker)
        self.pipeline.add(self.tiler) 
        self.pipeline.add(self.nvvidconv)
        self.pipeline.add(self.filter)
        self.pipeline.add(self.nvvidconv1)
        self.pipeline.add(self.nvosd)
        if is_aarch64():
            self.pipeline.add(self.transform)
        self.pipeline.add(self.sink)

        print("Linking elements in the Pipeline")
        self.streammux.link(self.pgie)
        self.pgie.link(self.tracker)
        self.tracker.link(self.nvvidconv1)
        self.nvvidconv1.link(self.filter)
        self.filter.link(self.tiler)
        self.tiler.link(self.nvvidconv)
        self.nvvidconv.link(self.nvosd)
        if is_aarch64():
            self.nvosd.link(self.transform)
            self.transform.link(self.sink)
        else:
            self.nvosd.link(self.sink)

    
    