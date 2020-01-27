class LaserException(Exception):
	pass

class Laser:
	def on(self):
		raise NotImplemented()
	
	def off(self):
		raise NotImplemented()

class DummyLaser(Laser):
	def on(self):
		pass
	
	def off(self):
		pass

lasers = {"dummy": DummyLaser}
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
		raise LaserException("Laser not installed '{}'".format(name))
	return lasers[name](**kwargs)
