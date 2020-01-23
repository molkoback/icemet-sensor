from icemet_sensor.worker import Worker

from icemet.io import File
from icemet.img import save_image

from datetime import datetime
import os
import time

class Saver(Worker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs, name="SAVER", delay=0.001)
		self.stack = kwargs["stack"]
		self.start_time = kwargs.get("start_time", None)
		self._time_next = None
		self._frame = 1
		self._meas = 1
	
	def init(self):
		# Create path
		if not os.path.exists(self.cfg.save.path):
			self.log.info("Creating path '{}'".format(self.cfg.save.path))
			os.makedirs(self.cfg.save.path)
		self.log.info("Save path {}".format(self.cfg.save.path))
		
		# Set timers
		if self.start_time is None:
			self.start_time = datetime.now()
		self.log.info("Start time {}".format(self.start_time))
		self._time_next = datetime.timestamp(self.start_time)
	
	def loop(self):
		# Read the newest image
		res = self.stack.pop()
		if res is None or res.time < self._time_next:
			return True
		
		# Save image
		dt = datetime.utcfromtimestamp(res.time)
		f = File(self.cfg.sensor.id, dt, self._frame)
		save_image(self.cfg.save.tmp, res.image)
		path = f.path(root=self.cfg.save.path, ext=self.cfg.save.type, subdirs=False)
		os.rename(self.cfg.save.tmp, path)
		self.log.info("SAVED {}".format(f.name))
		
		# Update counters
		self._time_next += self.cfg.meas.delay
		self._frame = self._frame % self.cfg.meas.len + 1
		self._meas += int(self._frame == 1)
		return self._meas <= self.cfg.meas.n
