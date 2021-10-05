from icemet_sensor.sensor import Sensor
from icemet_sensor.util import datetime_utc

from icemet.img import Image, BGSubStack
from icemet.file import FileStatus
from icemet.pkg import create_package

import cv2

import asyncio
import concurrent
from datetime import datetime
import logging
import os
import time

class MeasureException(Exception):
	pass

class Measure:
	def __init__(self, ctx):
		self.ctx = ctx
		self.sensor = Sensor(ctx.cfg)
		self._time_next = 0
		self._frame = 1
		self._meas = 1
		self._pkg = None
		self._bgsub = None
		len = self.ctx.cfg.preproc.bgsub_stack_len
		if len > 0:
			self._bgsub = BGSubStack(len)
		self._pool = concurrent.futures.ThreadPoolExecutor()
	
	def _is_empty(self, img):
		th = self.ctx.cfg.preproc.empty_th
		return th > 0 and img.dynrange() < th
	
	async def _show(self, img):
		def func():
			f = 640 / img.mat.shape[1]
			mat = cv2.resize(img.mat, dsize=None, fx=f, fy=f, interpolation=cv2.INTER_NEAREST)
			cv2.imshow("ICEMET-sensor", mat)
			cv2.waitKey(1)
		await self.ctx.loop.run_in_executor(self._pool, func)
	
	async def _preproc(self, img):
		# Crop
		shape_h, shape_w = img.mat.shape
		crop = self.ctx.cfg.preproc.crop
		if crop.w != shape_w or crop.h != shape_h:
			img.mat = img.mat[crop.y:crop.y+crop.h, crop.x:crop.x+crop.w]
		
		# Rotate
		rot = self.ctx.cfg.preproc.rotate
		if rot != 0:
			img.mat = img.rotate(rot)
		
		# Background subtraction
		if not self._bgsub is None:
			if not self._bgsub.push(img):
				return None
			img = self._bgsub.current()
			if img.datetime < datetime_utc(self._time_next):
				return None
			if self.ctx.args.image:
				await self._show(img)
			img = self._bgsub.meddiv()
		
		# Empty check
		if self._is_empty(img):
			img.status = FileStatus.EMPTY
		return img
	
	def _update_package(self, img):
		self._pkg.len += 1
		
		if img.status == FileStatus.NOTEMPTY:
			self._pkg.add_img(img)
			self._pkg.status = FileStatus.NOTEMPTY
		
		if img.frame == self.ctx.cfg.meas.burst_len:
			t = time.time()
			self._pkg.save(self.ctx.cfg.save.tmp)
			path = self._pkg.path(root=self.ctx.cfg.save.dir, ext=self.ctx.cfg.save.ext, subdirs=False)
			os.rename(self.ctx.cfg.save.tmp, path)
			logging.debug("Saved {} ({:.2f} s)".format(self._pkg.name(), time.time()-t))
			self._pkg = None
	
	def _save_image(self, img):
		if img.status == FileStatus.EMPTY:
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
		img = Image(
			sensor_id=self.ctx.cfg.sensor.id,
			datetime=res.datetime,
			frame=0,
			status=FileStatus.NOTEMPTY,
			mat=res.image
		)
		
		# Preprocess
		if self.ctx.cfg.preproc.enable:
			t = time.time()
			img = await self._preproc(img)
			logging.debug("Preprocessed ({:.2f} s)".format(time.time()-t))
			if img is None:
				return
			img.frame = self._frame
		else:
			if img.datetime < datetime_utc(self._time_next):
				return
			if self.ctx.args.image:
				await self._show(img)
			img.frame = self._frame
		
		# Create package
		if self.ctx.cfg.save.is_pkg and self._pkg is None:
			self._pkg = create_package(
				self.ctx.cfg.save.type.name,
				sensor_id=self.ctx.cfg.sensor.id,
				datetime=img.datetime,
				status=FileStatus.EMPTY,
				len=0,
				fps=self.ctx.cfg.meas.burst_fps,
				**self.ctx.cfg.save.type.kwargs
			)
		
		# Save or put in the package
		if self.ctx.cfg.save.is_pkg:
			task = self._update_package
		else:
			task = self._save_image
		await self.ctx.loop.run_in_executor(self._pool, task, img)
		logging.info("{}".format(img.name()))
		self._update_counters()
	
	async def _run(self):
		# Create path
		if not os.path.exists(self.ctx.cfg.save.dir):
			logging.info("Creating path '{}'".format(self.ctx.cfg.save.dir))
			os.makedirs(self.ctx.cfg.save.dir)
		logging.info("Save path '{}'".format(self.ctx.cfg.save.dir))
		
		# Start sensor
		await self.sensor.on()
		
		# Set measurement start time
		now = int(time.time())
		if self.ctx.args.start:
			self._time_next = datetime.strptime(self._time_next, "%Y-%m-%d %H:%M:%S").timestamp()
		elif self.ctx.args.start_now:
			self._time_next = now
		else:
			self._time_next = now // 60 * 60 + 60
		dt = datetime.fromtimestamp(self._time_next)
		logging.info("Start time {}".format(dt.strftime("%Y-%m-%d %H:%M:%S")))
		
		# Run measurements
		while not self.ctx.quit.is_set():
			await self._cycle()
	
	async def run(self):
		try:
			await self._run()
		except KeyboardInterrupt:
			self.ctx.quit.set()
		except Exception as e:
			logging.error(str(e))
			self.ctx.quit.set()
		finally:
			await self.sensor.off()
			self.sensor.close()
