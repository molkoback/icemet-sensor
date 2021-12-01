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

temp_relays = {"dummy": DummyTempRelay}
try:
	from icemet_sensor.hw.xyt01 import XYT01
	temp_relays["xyt01"] = XYT01
except:
	pass

def create_temp_relay(name, **kwargs):
	if not name in temp_relays:
		raise TempRelayException("Invalid TempRelay '{}'".format(name))
	return temp_relays[name](**kwargs)
