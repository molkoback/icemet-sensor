from icemet.img import BGSubStack, save_image, dynrange, rotate
from icemet.file import File, FileStatus
from icemet.pkg import create_package

import asyncio
from datetime import datetime, timezone
import logging
import os
import time

class Measure:
	def __init__(self, cfg, start_time, sensor):
		self.cfg = cfg
		self.sensor = sensor
		self.loop = asyncio.get_event_loop()
		self._time_next = start_time
		self._frame = 1
		self._meas = 1
		self._pkg_file = None
		if self.cfg.preproc.enable:
			size = (self.cfg.preproc.crop.h, self.cfg.preproc.crop.w)
			self._bgsub = BGSubStack(self.cfg.preproc.bgsub_stack_len, size)
			self._bgsub_files = []
	
	def _preproc(self, f):
		empty = self.cfg.preproc.empty
		crop = self.cfg.preproc.crop
		
		if empty.th_original > 0 and dynrange(f.image) < empty.th_original:
			logging.debug("Empty image")
			return None
		
		f.image = f.image[crop.y:crop.y+crop.h, crop.x:crop.x+crop.w]
		
		if self.cfg.preproc.rotate != 0:
			f.image = rotate(f.image, self.cfg.preproc.rotate)
		
		self._bgsub.push(f.image)
		self._bgsub_files.append(f)
		if not self._bgsub.full:
			return None
		f = self._bgsub_files[len(self._bgsub_files)//2]
		self._bgsub_files.pop(0)
		f.image = self._bgsub.meddiv()
		
		if empty.th_preproc > 0 and dynrange(f.image) < empty.th_preproc:
			logging.debug("Empty image")
			return None
		return f
	
	async def _update_package(self, f):
		if not f is None:
			self._pkg_file.package.add_file(f)
			self._pkg_file.status = FileStatus.NOTEMPTY
		if self._frame == self.cfg.meas.burst_len:
			t = time.time()
			self._pkg_file.package.save(self.cfg.save.tmp)
			path = self._pkg_file.path(root=self.cfg.save.dir, ext=self.cfg.save.ext, subdirs=False)
			os.rename(self.cfg.save.tmp, path)
			logging.debug("Saved {} ({:.2f} s)".format(f.name, time.time()-t))
	
	async def _save_file(self, f):
		t = time.time()
		save_image(self.cfg.save.tmp, f.image)
		path = f.path(root=self.cfg.save.dir, ext=self.cfg.save.ext, subdirs=False)
		os.rename(self.cfg.save.tmp, path)
		logging.debug("Saved {} ({:.2f} s)".format(f.name, time.time()-t))
	
	def _update_counters(self):
		self._time_next += self.cfg.meas.burst_delay
		self._frame = self._frame + 1
		if self._frame > self.cfg.meas.burst_len:
			self._frame = 1
			self._meas += 1
			self._time_next += self.cfg.meas.wait
	
	async def _cycle(self):
		# Read the newest image
		res = await self.sensor.read()
		if res.time < self._time_next:
			return
		
		# Create file
		dt = datetime.fromtimestamp(res.time, timezone.utc)
		f = File(self.cfg.sensor.id, dt, self._frame, status=FileStatus.NOTEMPTY, image=res.image)
		
		# Create package
		if self.cfg.save.is_pkg and self._frame == 1:
			pkg = create_package(
				self.cfg.save.type,
				fps=self.cfg.meas.burst_fps,
				len=self.cfg.meas.burst_len
			)
			self._pkg_file = File(self.cfg.sensor.id, dt, 0, status=FileStatus.EMPTY, package=pkg)
		
		# Preprocess
		if self.cfg.preproc.enable:
			t = time.time()
			f = self._preproc(f)
			logging.debug("Preprocessed ({:.2f} s)".format(time.time()-t))
		
		# Save or put in the package
		if self.cfg.save.is_pkg:
			self.loop.create_task(self._update_package(f))
		elif not f is None:
			self.loop.create_task(self._save_file(f))
		logging.info("{}".format(f.name))
		self._update_counters()
	
	async def run(self):
		# Create path
		if not os.path.exists(self.cfg.save.dir):
			logging.info("Creating path '{}'".format(self.cfg.save.dir))
			os.makedirs(self.cfg.save.dir)
		logging.info("Save path '{}'".format(self.cfg.save.dir))
		
		# Start the sensor
		await self.sensor.on()
		
		dt = datetime.fromtimestamp(self._time_next)
		logging.info("Start time {}".format(dt.strftime("%Y-%m-%d %H:%M:%S")))
		while True:
			await self._cycle()
			await asyncio.sleep(0.001)
