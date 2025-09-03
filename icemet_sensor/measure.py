from icemet_sensor.sensor import Sensor
from icemet_sensor.util import datetime_utc, logger

from icemet.img import Image, BGSubStack, CombineStack
from icemet.file import FileStatus

import torchvision.transforms.functional as tf
from torchvision.transforms import InterpolationMode

import asyncio
from datetime import datetime
import time

class MeasureException(Exception):
	pass

class Measure:
	def __init__(self, ctx):
		self.ctx = ctx
		self.sensor = Sensor(self.ctx.cfg)
		bgsub_len = self.ctx.cfg.get("BGSUB_STACK_LEN", 0)
		bgsub_use_middle = self.ctx.cfg.get("BGSUB_STACK_USE_MIDDLE", True)
		self._bgsub = BGSubStack(bgsub_len, bgsub_use_middle) if bgsub_len > 0 else None
		self._combine_len = self.ctx.cfg.get("COMBINE_STACK_LEN", 0)
		self._combine = None
		
		self._time_next = 0
		self._frame = 1
		self._meas = 1
	
	def _is_empty(self, img):
		th = self.ctx.cfg.get("EMPTY_TH", 0)
		return th > 0 and img.dynrange() < th
	
	async def _preproc(self, img):
		# Crop
		crop = self.ctx.cfg.get("CROP", None)
		if not crop is None:
			img.crop(crop["x"], crop["y"], crop["w"], crop["h"])
		
		# Scale
		scale = self.ctx.cfg.get("SCALE", None)
		if not scale is None:
			img.scale(scale["w"], scale["h"])
		
		# Rotate
		angle = self.ctx.cfg.get("ROTATE", 0)
		if angle != 0:
			img.rotate(angle)
		
		# Background subtraction
		if not self._bgsub is None:
			if not self._bgsub.push(img):
				return None
			if self._bgsub.current().datetime < datetime_utc(self._time_next):
				return None
			img = self._bgsub.meddiv()
			
			# Combine images
			if self._combine_len > 1:
				if self._combine is None:
					self._combine = CombineStack(self._combine_len)
				if not self._combine.push(img):
					return None
				img = self._combine.combine()
				self._combine = None
		
		# Empty check
		if self._is_empty(img):
			img.status = FileStatus.EMPTY
		return img
	
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
			data=res.image,
			params=res.params
		)
		
		# Preprocess
		t = time.time()
		img = await self._preproc(img)
		logger.debug("Preprocessed ({:.2f} s)".format(time.time()-t))
		if img is None or img.datetime < datetime_utc(self._time_next):
			return
		img.frame = self._frame
		
		await self.ctx.plugins.call("on_image", self.ctx, img)
		logger.info("{}".format(img.name()))
		self._update_counters()
	
	async def _run(self):
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
		logger.info("Start time {}".format(dt.strftime("%Y-%m-%d %H:%M:%S")))
		
		# Run measurements
		while not self.ctx.quit.is_set():
			await self._cycle()
	
	async def run(self):
		try:
			await self._run()
		except KeyboardInterrupt:
			pass
		except Exception as e:
			logger.error(str(e))
		self._pkg = None
		await self.sensor.off()
		self.sensor.close()
		self.ctx.quit.set()
