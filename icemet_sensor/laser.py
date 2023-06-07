import logging

class LaserException(Exception):
	pass

class Laser:
	async def on(self) -> None:
		raise NotImplementedError()
	
	async def off(self) -> None:
		raise NotImplementedError()
	
	def _close(self) -> None:
		raise NotImplementedError()
	
	def close(self):
		try:
			self._close()
		except NotImplementedError:
			pass
		except:
			logging.debug("Failed to close Laser")

class DummyLaser(Laser):
	async def on(self):
		pass
	
	async def off(self):
		pass

def create_laser(name, **kwargs):
	cls = None
	try:
		if name == "dummy":
			cls = DummyLaser
		elif name == "icemet":
			from icemet_sensor.hw.icemet_laser import ICEMETLaser
			cls = ICEMETLaser
		elif name == "myrio":
			from icemet_sensor.hw.myrio import MyRIO
			cls = MyRIO
		elif name == "picolas":
			from icemet_sensor.hw.picolas import PicoLAS
			cls = PicoLAS
	except:
		raise LaserException("Laser not installed '{}'".format(name))
	if cls is None:
		raise LaserException("Invalid Laser '{}'".format(name))
	return cls(**kwargs)
