class CameraException(Exception):
	pass

class Camera:
	def start(self):
		raise NotImplemented()
	
	def stop(self):
		raise NotImplemented()
	
	def read(self):
		raise NotImplemented()
	
	def params(self):
		raise NotImplemented()
	
	def set_params(self, d):
		raise NotImplemented()

cameras = {}
try:
	from icemet_sensor.camera.spin import SpinCamera
	cameras["spin"] = SpinCamera
except:
	pass

def createCamera(name, **kwargs):
	if not name in cameras:
		raise CameraException("Invalid camera '{}'".format(name))
	return cameras[name](**kwargs)
