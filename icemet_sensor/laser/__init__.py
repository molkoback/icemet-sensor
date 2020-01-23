class LaserException(Exception):
	pass

class Laser:
	def on(self):
		raise NotImplemented()
	
	def off(self):
		raise NotImplemented()

lasers = {}
try:
	from icemet_sensor.laser.icemet_laser import ICEMETLaser
	lasers["icemet"] = ICEMETLaser
except:
	pass
try:
	from icemet_sensor.laser.picolas import PicoLAS
	lasers["picolas"] = PicoLAS
except:
	pass

def createLaser(name, **kwargs):
	if not name in lasers:
		raise LaserException("Invalid laser '{}'".format(name))
	return lasers[name](**kwargs)
