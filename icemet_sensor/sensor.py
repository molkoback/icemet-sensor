from icemet_sensor.camera import create_camera
from icemet_sensor.laser import create_laser

import logging
import multiprocessing as mp
import time

class Sensor:
	def __init__(self, cfg):
		self.cfg = cfg
		self._lsr = None
		self._cam = None
		self._lsr = create_laser(self.cfg.laser.name, **self.cfg.laser.kwargs)
		self._cam = create_camera(self.cfg.camera.name, **self.cfg.camera.kwargs)
	
	async def on(self):
		await self._lsr.on()
		await self._cam.start()
		logging.debug("Sensor online")
	
	async def off(self):
		await self._cam.stop()
		await self._lsr.off()
		logging.debug("Sensor offline")
	
	async def read(self):
		t = time.time()
		res = await self._cam.read()
		logging.debug("Image read ({:.2f} s)".format(time.time()-t))
		return res
	
	def close(self):
		if not self._lsr is None:
			self._lsr.close()
		if not self._cam is None:
			self._cam.close()
