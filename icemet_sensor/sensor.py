from icemet_sensor.camera import create_camera, CameraException
from icemet_sensor.laser import create_laser
from icemet_sensor.temp_relay import create_temp_relay

import numpy as np

import asyncio
import logging
import time

class SensorException(Exception):
	pass

class Sensor:
	def __init__(self, cfg):
		self.cfg = cfg
		self._lsr = None
		self._cam = None
		self._lsr = create_laser(self.cfg.laser.name, **self.cfg.laser.kwargs)
		self._cam = create_camera(self.cfg.camera.name, **self.cfg.camera.kwargs)
		self._temp_relay = None
		if not self.cfg.temp_relay is None:
			self._temp_relay = create_temp_relay(self.cfg.temp_relay.name, **self.cfg.temp_relay.kwargs)
		self._on = False
	
	def _is_black(self, image):
		th = self.cfg.sensor.black_th
		return th > 0 and np.mean(image) < th
	
	async def on(self):
		if not self._on:
			await self._lsr.on()
			await self._cam.start()
			if not self._temp_relay is None:
				await self._temp_relay.enable()
			self._on = True
		logging.debug("Sensor ON")
	
	async def off(self):
		if self._on:
			await self._cam.stop()
			await self._lsr.off()
			self._on = False
		logging.debug("Sensor OFF")
	
	async def read(self):
		t = time.time()
		while time.time() - t < self.cfg.sensor.timeout:
			try:
				res = await self._cam.read()
				if not self._is_black(res.image):
					logging.debug("Image read ({:.2f} s)".format(time.time()-t))
					return res
			except CameraException as e:
				self._on = False
				raise e
		self._on = False
		raise SensorException("Sensor failed (black image)")
	
	async def temp(self):
		if self._temp_relay is None:
			return None
		return await self._temp_relay.temp()
	
	def close(self):
		if not self._lsr is None:
			self._lsr.close()
		if not self._cam is None:
			self._cam.close()
		if not self._temp_relay is None:
			self._temp_relay.close()
