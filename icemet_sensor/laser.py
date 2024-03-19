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

lasers = {
	"dummy": DummyLaser
}

def create_laser(name, **kwargs):
	cls = lasers.get(name, None)
	if cls is None:
		raise LaserException("Laser not installed '{}'".format(name))
	return cls(**kwargs)
