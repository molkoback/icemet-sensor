from icemet_sensor.worker import Worker

from icemet.img import BGSubStack, dynrange, rotate
from icemet.file import File

from datetime import datetime
import os
import time

class Manager(Worker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs, name="SAVER", delay=0.001)
		self.stack = kwargs["stack"]
		self.start_time = kwargs.get("start_time", None)
		self._time_next = None
		self._frame = 1
		self._meas = 1
		
		if self.cfg.preproc.enable:
			size = (self.cfg.preproc.crop.h, self.cfg.preproc.crop.w)
			self._bgsub = BGSubStack(self.cfg.preproc.bgsub_stack_len, size)
			self._files = []
	
	def init(self):
		# Create path
		if not os.path.exists(self.cfg.save.dir):
			self.log.info("Creating path '{}'".format(self.cfg.save.dir))
			os.makedirs(self.cfg.save.dir)
		self.log.info("Save path '{}'".format(self.cfg.save.dir))
		
		# Set timers
		if self.start_time is None:
			self.start_time = datetime.now()
		self.log.info("Start time {}".format(self.start_time))
		self._time_next = datetime.timestamp(self.start_time)
	
	def _preproc(self, f):
		empty = self.cfg.preproc.empty
		crop = self.cfg.preproc.crop
		
		if empty.th_original > 0 and dynrange(f.image) < empty.th_original:
			self.log.debug("Empty image")
			return False, None, None
		
		f.image = f.image[crop.y:crop.y+crop.h, crop.x:crop.x+crop.w]
		
		if self.cfg.preproc.rotate != 0:
			f.image = rotate(f.image, self.cfg.preproc.rotate)
		
		self._bgsub.push(f.image)
		self._files.append(f)
		if not self._bgsub.full:
			return False, None, None
		f = self._files[len(self._files)//2]
		self._files.pop(0)
		f.image = self._bgsub.meddiv()
		
		if empty.th_preproc > 0 and dynrange(f.image) < empty.th_preproc:
			self.log.debug("Empty image")
			return False, None, None
		return True, f
	
	def _update_counters(self):
		self._time_next += self.cfg.meas.burst_delay
		self._frame = self._frame + 1
		if self._frame > self.cfg.meas.burst_len:
			self._frame = 1
			self._meas += 1
			self._time_next += self.cfg.meas.wait
	
	def loop(self):
		# Read the newest image
		res = self.stack.pop()
		if res is None or res.time < self._time_next:
			return True
		
		# Create file
		dt = datetime.utcfromtimestamp(res.time)
		f = File(self.cfg.sensor.id, dt, self._frame, image=res.image)
		
		# Preprocess
		if self.cfg.preproc.enable:
			t = time.time()
			ret, f = self._preproc(f)
			self.log.debug("Preprocessed ({:.2f} s)".format(time.time()-t))
			if not ret:
				self._update_counters()
				return True
		
		# Save image
		t = time.time()
		f.save(self.cfg.save.tmp)
		path = f.path(root=self.cfg.save.dir, ext=self.cfg.save.type, subdirs=False)
		os.rename(self.cfg.save.tmp, path)
		self.log.debug("Saved {} ({:.2f} s)".format(f.name, time.time()-t))
		self.log.info("{}".format(f.name))
		self._update_counters()
		return self._meas <= self.cfg.meas.n
