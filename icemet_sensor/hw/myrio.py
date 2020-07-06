from icemet_sensor.laser import Laser

import psutil

import logging
import os
import subprocess as sp
import time

class MyRIO(Laser):
	def __init__(self, saku_laser_path="C:/SAKU Laser"):
		self._pid = None
		self._cmd = [os.path.join(saku_laser_path, "SAKU Laser.exe")]
	
	def __del__(self):
		self._kill()
	
	def on(self):
		self._pid = sp.Popen(self._cmd).pid
		logging.info("Waiting for SAKU Laser")
		time.sleep(10)
	
	def _kill(self):
		if not self._pid is None:
			psutil.Process(self._pid).kill()
			self._pid = None
	
	def off(self):
		self._kill()
