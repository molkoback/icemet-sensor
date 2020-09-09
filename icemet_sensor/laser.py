class LaserException(Exception):
	pass

class Laser:
	async def on(self) -> None:
		raise NotImplementedError()
	
	async def off(self) -> None:
		raise NotImplementedError()
	
	def close(self) -> None:
		raise NotImplementedError()

class DummyLaser(Laser):
	async def on(self):
		pass
	
	async def off(self):
		pass
	
	def close(self):
		pass

lasers = {"dummy": DummyLaser}
try:
	from icemet_sensor.hw.icemet_laser import ICEMETLaser
	lasers["icemet"] = ICEMETLaser
except:
	pass
try:
	from icemet_sensor.hw.myrio import MyRIO
	lasers["myrio"] = MyRIO
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
