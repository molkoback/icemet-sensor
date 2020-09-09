from icemet_sensor.sensor import Sensor

from icemet.img import Image, BGSubStack
from icemet.file import FileStatus
from icemet.pkg import create_package

import asyncio
from datetime import datetime, timezone
import logging
import os
import time

class Measure:
	def __init__(self, ctx, start_time):
		self.ctx = ctx
		self.sensor = Sensor(ctx.cfg)
		self._time_next = start_time
		self._frame = 1
		self._meas = 1
		self._pkg = None
		if self.ctx.cfg.preproc.enable:
			size = (self.ctx.cfg.preproc.crop.h, self.ctx.cfg.preproc.crop.w)
			self._bgsub = BGSubStack(self.ctx.cfg.preproc.bgsub_stack_len, size)
	
	def _preproc(self, img):
		empty = self.ctx.cfg.preproc.empty
		crop = self.ctx.cfg.preproc.crop
		
		if empty.th_original > 0 and img.dynrange() < empty.th_original:
			img.status = FileStatus.EMPTY
			return img
		
		img.mat = img.mat[crop.y:crop.y+crop.h, crop.x:crop.x+crop.w]
		
		if self.ctx.cfg.preproc.rotate != 0:
			img.mat = img.rotate(self.ctx.cfg.preproc.rotate)
		
		self._bgsub.push(img)
		if not self._bgsub.full:
			return None
		img = self._bgsub.meddiv()
		
		if empty.th_preproc > 0 and img.dynrange() < empty.th_preproc:
			img.status = FileStatus.EMPTY
		return img
	
	def _update_package(self, img):
		self._pkg.len += 1
		
		if img.status == FileStatus.EMPTY:
			logging.debug("Empty image")
		else:
			self._pkg.add_img(img)
			self._pkg.status = FileStatus.NOTEMPTY
		
		if img.frame == self.ctx.cfg.meas.burst_len:
			t = time.time()
			self._pkg.save(self.ctx.cfg.save.tmp)
			path = self._pkg.path(root=self.ctx.cfg.save.dir, ext=self.ctx.cfg.save.ext, subdirs=False)
			os.rename(self.ctx.cfg.save.tmp, path)
			logging.debug("Saved {} ({:.2f} s)".format(self._pkg.name(), time.time()-t))
			self._pkg = None
	
	def _save_img(self, img):
		if img.status == FileStatus.EMPTY:
			logging.debug("Empty image")
			return
		t = time.time()
		img.save(self.ctx.cfg.save.tmp)
		path = img.path(root=self.ctx.cfg.save.dir, ext=self.ctx.cfg.save.ext, subdirs=False)
		os.rename(self.ctx.cfg.save.tmp, path)
		logging.debug("Saved {} ({:.2f} s)".format(img.name(), time.time()-t))
	
	def _update_counters(self):
		self._time_next += self.ctx.cfg.meas.burst_delay
		self._frame = self._frame + 1
		if self._frame > self.ctx.cfg.meas.burst_len:
			self._frame = 1
			self._meas += 1
			self._time_next += self.ctx.cfg.meas.wait
	
	async def _cycle(self):
		# Read the newest image
		res = await self.sensor.read()
		if res.time < self._time_next:
			return
		
		# Create image
		dt = datetime.fromtimestamp(res.time, timezone.utc)
		img = Image(
			sensor_id=self.ctx.cfg.sensor.id,
			datetime=dt,
			frame=self._frame,
			status=FileStatus.NOTEMPTY,
			mat=res.image
		)
		
		# Create package
		if self.ctx.cfg.save.is_pkg and self._pkg is None:
			self._pkg = create_package(
				self.ctx.cfg.save.type,
				sensor_id=self.ctx.cfg.sensor.id,
				datetime=dt,
				frame=0,
				status=FileStatus.EMPTY,
				len=0,
				fps=self.ctx.cfg.meas.burst_fps
			)
		
		# Preprocess
		if self.ctx.cfg.preproc.enable:
			t = time.time()
			img = self._preproc(img)
			logging.debug("Preprocessed ({:.2f} s)".format(time.time()-t))
		
		# Save or put in the package
		if img is not None:
			if self.ctx.cfg.save.is_pkg:
				task = self._update_package
			else:
				task = self._save_img
			await self.ctx.loop.run_in_executor(None, task, img)
			logging.info("{}".format(img.name()))
		self._update_counters()
	
	async def run(self):
		# Create path
		if not os.path.exists(self.ctx.cfg.save.dir):
			logging.info("Creating path '{}'".format(self.ctx.cfg.save.dir))
			os.makedirs(self.ctx.cfg.save.dir)
		logging.info("Save path '{}'".format(self.ctx.cfg.save.dir))
		
		# Run measurements
		try:
			await self.sensor.on()
			dt = datetime.fromtimestamp(self._time_next)
			logging.info("Start time {}".format(dt.strftime("%Y-%m-%d %H:%M:%S")))
			while not self.ctx.quit.is_set():
				await self._cycle()
				await asyncio.sleep(0.001)
		except KeyboardInterrupt:
			self.ctx.quit.set()
		finally:
			await self.sensor.off()
			self.sensor.close()
