from os import read
import yaml
from yaml.loader import SafeLoader



class Configs:
    def __init__(self, pth_config):
        self.pth_cfg = pth_config
        info_cfg = self.read_config(self.pth_cfg)
        self.PGIE_CONFIG_FILE = info_cfg["PGIE_CONFIG_FILE"]
        self.TRACKER_CONFIG_FILE = info_cfg["TRACKER_CONFIG_FILE"]
        self.CONFIG_GPU_ID = info_cfg["CONFIG_GPU_ID"]

        ## tracker
        self.CONFIG_GROUP_TRACKER = info_cfg["CONFIG_GROUP_TRACKER"]
        self.CONFIG_GROUP_TRACKER_WIDTH = info_cfg["CONFIG_GROUP_TRACKER_WIDTH"]
        self.CONFIG_GROUP_TRACKER_HEIGHT = info_cfg["CONFIG_GROUP_TRACKER_HEIGHT"]
        self.CONFIG_GROUP_TRACKER_LL_CONFIG_FILE = info_cfg["CONFIG_GROUP_TRACKER_LL_CONFIG_FILE"]
        self.CONFIG_GROUP_TRACKER_LL_LIB_FILE = info_cfg["CONFIG_GROUP_TRACKER_LL_LIB_FILE"] 
        self.CONFIG_GROUP_TRACKER_ENABLE_BATCH_PROCESS = info_cfg["CONFIG_GROUP_TRACKER_ENABLE_BATCH_PROCESS"]
         

        ## streamux && tiler
        self.MUXER_OUTPUT_WIDTH = info_cfg["MUXER_OUTPUT_WIDTH"]
        self.MUXER_OUTPUT_HEIGHT = info_cfg["MUXER_OUTPUT_HEIGHT"]
        self.MUXER_BATCH_TIMEOUT_USEC = info_cfg["MUXER_BATCH_TIMEOUT_USEC"]
        self.TILED_OUTPUT_WIDTH = info_cfg["TILED_OUTPUT_WIDTH"]
        self.TILED_OUTPUT_HEIGHT = info_cfg["TILED_OUTPUT_HEIGHT"]
        self.GST_CAPS_FEATURES_NVMM = info_cfg["GST_CAPS_FEATURES_NVMM"]

        ## det 
        self.MIN_CONFIDENCE = info_cfg["MIN_CONFIDENCE"]
        self.MAX_CONFIDENCE = info_cfg["MAX_CONFIDENCE"]
        self.PGIE_CLASS_ID_PERSON = info_cfg["PGIE_CLASS_ID_PERSON"]
        self.pgie_classes_str = info_cfg["pgie_classes_str"]

        ## max source 
        self.MAX_NUM_SOURCES = info_cfg["MAX_NUM_SOURCES"]
        self.GPU_ID = info_cfg["GPU_ID"]

    def read_config(self, pth_cfg):
        with open(pth_cfg) as f:
            data = yaml.load(f, Loader=SafeLoader)
        f.close()
        # print(data)clear
        
        return data
    
configs = Configs(pth_config="dev_cfg.yaml")