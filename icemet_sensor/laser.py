class LaserException(Exception):
	pass

class Laser:
	def on(self) -> None:
		raise NotImplementedError()
	
	def off(self) -> None:
		raise NotImplementedError()

class DummyLaser(Laser):
	def on(self):
		pass
	
	def off(self):
		pass

lasers = {"dummy": DummyLaser}
try:
	from icemet_sensor.hw.icemet_laser import ICEMETLaser
	lasers["icemet"] = ICEMETLaser
except:
	pass
try:
	from icemet_sensor.hw.picolas import PicoLAS
	lasers["picolas"] = PicoLAS
except:
	pass

def create_laser(name, **kwargs):
	if not name in lasers:
		raise LaserException("Laser not installed '{}'".format(name))
	return lasers[name](**kwargs)
