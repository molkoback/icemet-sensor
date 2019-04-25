from icemet.file import File
from icemet.worker import Worker

import cv2

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
			self.log.info("Creating path '%s'" % self.cfg.save.path)
			os.makedirs(self.cfg.save.path)
		self.log.info("Save path %s" % self.cfg.save.path)
		
		# Set timers
		if self.start_time is None:
			self.start_time = datetime.now()
		self.log.info("Start time %s" % self.start_time)
		self._time_next = datetime.timestamp(self.start_time)
	
	def loop(self):
		# Read the newest image
		im = self.stack.pop()
		if im is None or im.stamp < self._time_next:
			return True
		
		# Save image
		dt = datetime.utcfromtimestamp(im.stamp)
		f = File(self.cfg.sensor.id, dt, self._frame, False)
		cv2.imwrite(self.cfg.save.tmp, im.data)
		os.rename(self.cfg.save.tmp, f.path(self.cfg.save.path, self.cfg.save.type))
		self.log.info("SAVED %s" % f)
		
		# Update counters
		self._time_next += self.cfg.meas.delay
		self._frame = self._frame % self.cfg.meas.len + 1
		self._meas += int(self._frame == 1)
		return self._meas <= self.cfg.meas.n
