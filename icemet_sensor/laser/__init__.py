class LaserException(Exception):
	pass

class Laser:
	def on(self):
		raise NotImplemented()
	
	def off(self):
		raise NotImplemented()

from icemet_sensor.laser.icemet_laser import ICEMETLaser
from icemet_sensor.laser.picolas import PicoLAS

_lasers = {
	"icemet": ICEMETLaser,
	"picolas": PicoLAS
}

def createLaser(name, **kwargs):
	if not name in _lasers:
		raise LaserException("Invalid laser '{}'".format(name))
	return _lasers[name](**kwargs)
