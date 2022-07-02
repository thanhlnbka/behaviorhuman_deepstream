from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


class HumanBehavior:
    def __init__(self,timestampID,cam_id):
        self.timestamp = timestampID # class timestampID
        self.cam_id = cam_id
        self.polygon = self.read_polygon()

    def update_polygon(self):
        new_polygon = []
        self.polygon = new_polygon
         


    def read_polygon(self):
        polygon = [(0,0),(1920,0),(1920,1080),(0,1080)]
        return polygon
    
    @staticmethod
    def point_inside_polygon(point, polygon):
        point_check = Point(point)
        polygon_check = Polygon(polygon)
        return polygon_check.contains(point_check)


    def waring_with_time(self, id, time_warning):
        times = self.timestamp.get_times_id(id)
        boxes = self.timestamp.get_boxes_id(id)
        box_current = boxes[-1]
        point_center = ((box_current[0]+box_current[2])/2,(box_current[1]+box_current[3])/2 )
        if self.point_inside_polygon(point = point_center, polygon = self.polygon):
            if (times[-1] - times[0]) <= time_warning:
                return True
        return False

    def loitering(self, id, time_warning):
        warn = self.waring_with_time(id, time_warning)
        return warn
 
    def intrusion(self, id, time_warning):
        warn = self.waring_with_time(id, time_warning)
        return warn

    def crowdhuman(self, id, time_warning):
        pass 

