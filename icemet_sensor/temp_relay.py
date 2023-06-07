import logging

class TempRelayException(Exception):
	pass

class TempRelay:
	async def temp(self) -> (float, float):
		raise NotImplementedError()
	
	async def enable(self) -> None:
		raise NotImplementedError()
	
	async def disable(self) -> None:
		raise NotImplementedError()
	
	def _close(self) -> None:
		raise NotImplementedError()
	
	def close(self):
		try:
			self._close()
		except NotImplementedError:
			pass
		except:
			logging.debug("Failed to close TempRelay")

class DummyTempRelay(TempRelay):
	async def temp(self):
		return 20.0, 0.0
	
	async def enable(self):
		pass
	
	async def disable(self):
		pass

def create_temp_relay(name, **kwargs):
	cls = None
	try:
		if name == "dummy":
			cls  = DummyTempRelay
		elif name == "xyt01":
			from icemet_sensor.hw.xyt01 import XYT01
			cls  = XYT01
	except:
		raise TempRelayException("TempRelay not installed '{}'".format(name))
	if cls is None:
		raise TempRelayException("Invalid TempRelay '{}'".format(name))
	return cls(**kwargs)
