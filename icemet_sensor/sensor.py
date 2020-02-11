from icemet_sensor.camera import CameraResult, createCamera
from icemet_sensor.data import Stack
from icemet_sensor.laser import createLaser
from icemet_sensor.worker import Worker

from icemet.img import BGSubStack, dynrange, rotate

import time

class Sensor(Worker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs, name="SENSOR")
		self.stack = kwargs.get("stack", Stack(10))
		
		if self.cfg.preproc.enable:
			size = (self.cfg.preproc.crop.h, self.cfg.preproc.crop.w)
			self.bgsub = BGSubStack(self.cfg.preproc.bgsub_stack_len, size)
			self.stamps = []
		
		self._lsr = None
		self._cam = None
		self._start_time = None
	
	def _start(self):
		self._lsr.on()
		self._cam.start()
		self._start_time = time.time()
		self.log.debug("Sensor started")
	
	def _stop(self):
		self._cam.stop()
		self._lsr.off()
		self._start_time = None
		self.log.debug("Sensor stopped")
	
	def _preproc(self, res):
		im = res.image
		stamp = res.time
		empty = self.cfg.preproc.empty
		crop = self.cfg.preproc.crop
		
		if empty.th_original > 0 and dynrange(im) < empty.th_original:
			return None
		
		im = im[crop.y:crop.y+crop.h, crop.x:crop.x+crop.w]
		
		if self.cfg.preproc.rotate != 0:
			im = rotate(im, self.cfg.preproc.rotate)
		
		self.bgsub.push(im)
		self.stamps.append(stamp)
		stamp = self.stamps.pop(0)
		if not self.bgsub.full:
			return None
		im = self.bgsub.meddiv()
		
		if empty.th_preproc > 0 and dynrange(im) < empty.th_preproc:
			return None
		return CameraResult(image=im, time=stamp)
	
	def init(self):
		self._lsr = createLaser(self.cfg.laser.name, **self.cfg.laser.kwargs)
		self._cam = createCamera(self.cfg.camera.name, **self.cfg.camera.kwargs)
		self._start()
	
	def loop(self):
		if self.cfg.sensor.restart >= 0 and time.time() - self._start_time > self.cfg.sensor.restart:
			self.stop()
			self.start()
		
		res = self._cam.read()
		self.log.debug("Image taken")
		
		if not self.cfg.preproc.enable:
			self.stack.push(res)
		else:
			res = self._preproc(res)
			if not res is None:
				self.stack.push(res)
		return True
	
	def cleanup(self):
		self._stop()
