class CameraException(Exception):
	pass

class CameraResult:
	def __init__(self, **kwargs):
		self.image = kwargs.get("image", None)
		self.time = kwargs.get("time", None)

class Camera:
	def start(self):
		raise NotImplemented()
	
	def stop(self):
		raise NotImplemented()
	
	def read(self):
		raise NotImplemented()
	
	def save_params(self, fn):
		raise NotImplemented()
	
	def load_params(self, fn):
		raise NotImplemented()

cameras = {}
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
