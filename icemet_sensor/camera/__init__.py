import numpy as np

import random
import time

class CameraException(Exception):
	pass

class CameraResult:
	def __init__(self, **kwargs):
		self.image = kwargs.get("image", None)
		self.time = kwargs.get("time", None)

class Camera:
	def start(self) -> None:
		raise NotImplemented()
	
	def stop(self) -> None:
		raise NotImplemented()
	
	def read(self) -> CameraResult:
		raise NotImplemented()
	
	def save_params(self, fn: str) -> None:
		raise NotImplemented()
	
	def load_params(self, fn: str) -> None:
		raise NotImplemented()

class DummyCamera:
	def __init__(self, size=(640, 480), low=0, high=255):
		self.size = size
		self.low = low
		self.high = high
	
	def start(self):
		pass
	
	def stop(self):
		pass
	
	def read(self):
		time.sleep(random.randint(1, 50)/1000)
		return CameraResult(
			image=np.random.randint(
				self.low, high=self.high,
				size=(self.size[1], self.size[0]),
				dtype=np.uint8
			),
			time=time.time()
		)

cameras = {"dummy": DummyCamera}
try:
	from icemet_sensor.camera.spin import SpinCamera
	cameras["spin"] = SpinCamera
except:
	pass
try:
	from icemet_sensor.camera.pylon import PylonCamera
	cameras["pylon"] = PylonCamera
except:
	pass

def createCamera(name, **kwargs):
	if not name in cameras:
		raise CameraException("Camera not installed '{}'".format(name))
	return cameras[name](**kwargs)
