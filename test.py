
import time
import socketio
import cv2
import json
import base64
from time import sleep
import queue 
queue_img = queue.Queue(maxsize=30)

def read_video():
	cap=cv2.VideoCapture("rtsp://admin:Comit123@192.168.6.108:554")
	while True:
		_, frame = cap.read()
		queue_img.put(frame)

# cap.set(cv2.CAP_PROP_FRAME_WIDTH , 352)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT , 288)
sio = socketio.Client(engineio_logger=False)
i=0
@sio.event
def connect():
	print("CONNECTED")

@sio.event
def send_data(): 
	while True:
		img = queue_img.get()
		if img is not None:
			# img = cv2.resize(img, (0,0), fx=0.5, fy=0.5)
			# img = cv2.resize(img, (480,360))
			frame = cv2.imencode('.jpg', img)[1].tobytes()
			frame= base64.encodebytes(frame).decode("utf-8")
			json = {"cam_id":1, "img_base64":frame }
			sio.emit('send',json)
		

@sio.event
def disconnect():
	print("DISCONNECTED")

if __name__ == '__main__':
	#sio.connect('http://192.168.0.108:5000') ## uncomment this line when the server is on remote system change the ip address with the ip address 
	#of the system where the server is running.
	import threading
	threading.Thread(target=read_video).start()
	sio.connect('http://0.0.0.0:5000')
	sio.wait()
