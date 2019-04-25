from icemet.camera import Camera
from icemet.data import Stack
from icemet.laser import Laser
from icemet.worker import Worker

import time

class Sensor(Worker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs, name="SENSOR")
		self.stack = kwargs.get("stack", Stack(10))
		
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
	
	def init(self):
		self._lsr = Laser(self.cfg.laser.port)
		self._cam = Camera(self.cfg.camera.id)
		self._start()
	
	def loop(self):
		if self.cfg.sensor.restart >= 0 and time.time() - self._start_time > self.cfg.sensor.restart:
			self.stop()
			self.start()
		self.stack.push(self._cam.read())
		self.log.debug("Image taken")
		return True
	
	def cleanup(self):
		self._stop()
