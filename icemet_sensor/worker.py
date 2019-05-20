from icemet_sensor.data import Atomic

import logging
import time
import threading

class Worker:
	def __init__(self, *args, **kwargs):
		self.cfg = kwargs.get("cfg", None)
		self.quit = kwargs.get("quit", Atomic(False))
		self.delay = kwargs.get("delay", 0.0)
		self.name = kwargs.get("name", "WORKER")
		self.log = logging.getLogger(self.name)
	
	def init(self):
		pass
	
	def loop(self):
		return False
	
	def cleanup(self):
		pass
	
	def run(self):
		self.log.debug("Running")
		try:
			self.init()
			while not self.quit.get() and self.loop():
				time.sleep(self.delay)
			self.cleanup()
			self.log.debug("Finished")
		except Exception as err:
			self.log.critical(str(err))
	
	@classmethod
	def start(cls, *args, **kwargs):
		worker = cls(*args, **kwargs)
		t = threading.Thread(target=worker.run)
		t.start()
		return t
