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

from icemet_sensor.camera.spin import SpinCamera

_cameras = {
	"spin": SpinCamera
}

def createCamera(name, **kwargs):
	if not name in _cameras:
		raise CameraException("Invalid camera '{}'".format(name))
	return _cameras[name](**kwargs)
