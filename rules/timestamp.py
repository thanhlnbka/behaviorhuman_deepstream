
class TimeStampID:
    def __init__(self,cam_id):
        self.infos = dict()
        self.cam_id = cam_id

    def put_info_id(self, id, time, box):
        if id not in self.infos:
            self.infos[id] = {"times":[time], "boxes":[box]}
        else:
            time_ = self.infos[id]["times"]
            box_ = self.infos[id]["boxes"]
            time_.append(time)
            box_.append(box)
            self.infos[id]["times"] = time_
            self.infos[id]["boxes"] = box_ 


    def get_times_id(self, id):
        return self.infos[id]["times"] 
    
    def get_boxes_id(self, id):
        return self.infos[id]["boxes"]

    def del_info_id(self, id):
        self.infos.pop(id)
        



if __name__=="__main__":
    import time 
    timestamp = TimeStampID(cam_id="1")
    [timestamp.put_info_id(1, time.time(),[12]) for i in range(5)]
    [timestamp.put_info_id(2, time.time(),[22]) for i in range(10)]
    print(timestamp.infos)
    timestamp.del_info_id(2)
    print(timestamp.infos)