from icemet_sensor.laser import Laser

import psutil

import asyncio
import logging
import os
import subprocess as sp

class MyRIO(Laser):
	def __init__(self, saku_laser_path="C:/SAKU Laser"):
		self._pid = None
		self._cmd = [os.path.join(saku_laser_path, "SAKU Laser.exe")]
	
	async def on(self):
		self._pid = sp.Popen(self._cmd).pid
		logging.info("Waiting for SAKU Laser")
		await asyncio.sleep(10)
	
	def _kill(self):
		if not self._pid is None:
			psutil.Process(self._pid).kill()
			self._pid = None
	
	async def off(self):
		self._kill()
	
	def _close(self):
		self._kill()
