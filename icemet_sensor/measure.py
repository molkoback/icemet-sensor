from icemet_sensor.sensor import Sensor
from icemet_sensor.util import datetime_utc, tmpfile

from icemet.img import Image, BGSubStack
from icemet.file import FileStatus
from icemet.pkg import create_package, name2ext

import cv2

import asyncio
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
		len = self.ctx.cfg.get("BGSUB_STACK_LEN", 0)
		self._bgsub = BGSubStack(len) if len > 0 else None
		ext = name2ext(self.ctx.cfg["FILE_TYPE"])
		self._file_is_pkg = bool(ext)
		self._file_ext = ext if ext else "."+self.ctx.cfg["FILE_TYPE"]
		
		self._time_next = 0
		self._frame = 1
		self._meas = 1
		self._pkg = None
	
	def _is_empty(self, img):
		th = self.ctx.cfg.get("EMPTY_TH", 0)
		return th > 0 and img.dynrange() < th
	
	async def _show(self, img):
		def func():
			f = 640 / img.mat.shape[1]
			mat = cv2.resize(img.mat, dsize=None, fx=f, fy=f, interpolation=cv2.INTER_NEAREST)
			cv2.imshow("ICEMET-sensor", mat)
			cv2.waitKey(1)
		await self.ctx.loop.run_in_executor(self.ctx.pool, func)
	
	async def _preproc(self, img):
		# Crop
		shape_w, shape_h = img.mat.shape[1], img.mat.shape[0]
		crop = self.ctx.cfg.get("CROP", {"x": 0, "y": 0, "w": shape_w, "h": shape_h})
		if crop["x"] != 0 or crop["y"] != 0 or crop["w"] != shape_w or crop["h"] != shape_h:
			img.mat = img.mat[crop["y"]:crop["y"]+crop["h"], crop["x"]:crop["x"]+crop["w"]]
		
		# Rotate
		rot = self.ctx.cfg.get("ROTATE", 0)
		if rot != 0:
			img.mat = img.rotate(rot)
		
		# Background subtraction
		if not self._bgsub is None:
			if not self._bgsub.push(img):
				return None
			if self._bgsub.current().datetime < datetime_utc(self._time_next):
				return None
			img = self._bgsub.meddiv()
		
		# Empty check
		if self._is_empty(img):
			img.status = FileStatus.EMPTY
		return img
	
	def _update_package(self, img):
		self._pkg.len += 1
		
		if img.status == FileStatus.NOTEMPTY:
			self._pkg.status = FileStatus.NOTEMPTY
		self._pkg.add_img(img)
		
		if img.frame == self.ctx.cfg["MEAS_LEN"]:
			tmp = os.path.join(self.ctx.cfg["SAVE_DIR"], tmpfile()+self._file_ext)
			dst = os.path.join(self.ctx.cfg["SAVE_DIR"], self._pkg.name()+self._file_ext)
			
			t = time.time()
			self._pkg.save(tmp)
			os.rename(tmp, dst)
			logging.debug("Saved {} ({:.2f} s)".format(self._pkg.name(), time.time()-t))
			self._pkg = None
	
	def _save_image(self, img):
		if img.status == FileStatus.EMPTY:
			return
		
		tmp = os.path.join(self.ctx.cfg["SAVE_DIR"], tmpfile()+self._file_ext)
		dst = os.path.join(self.ctx.cfg["SAVE_DIR"], img.name()+self._file_ext)
		
		t = time.time()
		img.save(tmp)
		os.rename(tmp, dst)
		logging.debug("Saved {} ({:.2f} s)".format(img.name(), time.time()-t))
	
	def _update_counters(self):
		self._time_next += 1.0 / self.ctx.cfg["MEAS_FPS"]
		self._frame = self._frame + 1
		if self._frame > self.ctx.cfg["MEAS_LEN"]:
			self._frame = 1
			self._meas += 1
			self._time_next += self.ctx.cfg["MEAS_WAIT"]
	
	async def _cycle(self):
		# Read the newest image
		res = await self.sensor.read()
		img = Image(
			sensor_id=self.ctx.cfg["SENSOR_ID"],
			datetime=res.datetime,
			frame=0,
			status=FileStatus.NOTEMPTY,
			mat=res.image
		)
		
		# Preprocess
		t = time.time()
		img = await self._preproc(img)
		logging.debug("Preprocessed ({:.2f} s)".format(time.time()-t))
		if img is None or img.datetime < datetime_utc(self._time_next):
			return
		img.frame = self._frame
		
		# Show image
		if self.ctx.args.image:
			await self._show(img)
		
		# Create package
		if self._file_is_pkg and self._pkg is None:
			self._pkg = create_package(
				self.ctx.cfg["FILE_TYPE"],
				sensor_id=self.ctx.cfg["SENSOR_ID"],
				datetime=img.datetime,
				status=FileStatus.EMPTY,
				len=0,
				fps=self.ctx.cfg["MEAS_FPS"],
				**self.ctx.cfg["FILE_OPT"]
			)
		
		# Save or put in the package
		if self._file_is_pkg:
			task = self._update_package
		else:
			task = self._save_image
		await self.ctx.loop.run_in_executor(self.ctx.pool, task, img)
		logging.info("{}".format(img.name()))
		self._update_counters()
	
	async def _run(self):
		# Create path
		if not os.path.exists(self.ctx.cfg["SAVE_DIR"]):
			logging.info("Creating path '{}'".format(self.ctx.cfg["SAVE_DIR"]))
			os.makedirs(self.ctx.cfg["SAVE_DIR"])
		logging.info("Save path '{}'".format(self.ctx.cfg["SAVE_DIR"]))
		
		# Start sensor
		await self.sensor.on()
		
		# Set measurement start time
		now = int(time.time())
		if self.ctx.args.start:
			self._time_next = datetime.strptime(self.ctx.args.start, "%Y-%m-%d %H:%M:%S").timestamp()
		elif self.ctx.args.start_now:
			self._time_next = now
		elif self.ctx.args.start_next_10min:
			self._time_next = now // 600 * 600 + 600
		elif self.ctx.args.start_next_hour:
			self._time_next = now // 3600 * 3600 + 3600
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
			pass
		except Exception as e:
			logging.error(str(e))
		self._pkg = None
		await self.sensor.off()
		self.sensor.close()
		self.ctx.quit.set()
