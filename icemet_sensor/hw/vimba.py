from icemet_sensor.camera import CameraResult, Camera, CameraException
from icemet_sensor.util import datetime_utc

import vimba

import asyncio
import concurrent.futures
import time
import threading

class VimbaCamera(Camera):
	def __init__(self, id=None, params=None, hwclock=True, timeout=1.0):
		self.ctx = vimba.Vimba.get_instance()
		with self.ctx:
			try:
				if id:
					self.cam = self.ctx.get_camera_by_id(id)
				else:
					self.cam = self.ctx.get_all_cameras()[0]
			except:
				raise CameraException("VimbaCamera not found")
		
		if params:
			self.load_params(params)
		
		self._result = None
		self._result_lock = threading.Lock()
		self._result_event = threading.Event()
		self._stop_event = asyncio.Event()
		
		self._loop = asyncio.get_event_loop()
		self._pool = concurrent.futures.ThreadPoolExecutor()
		
		self.hwclock = hwclock
		self.timeout = timeout
		self._start_time = None
		self._start_stamp = None
	
	def _datetime(self, frame):
		if not self.hwclock:
			return datetime_utc()
		
		stamp = frame.get_timestamp()
		if self._start_stamp is None or stamp < self._start_stamp:
			self._start_stamp = stamp
			self._start_time = time.time()
			return datetime_utc()
		
		_time = (stamp - self._start_stamp) / 10**9 + self._start_time
		return datetime_utc(_time)
	
	def _frame_handler(self, cam, frame):
		if frame.get_status() == vimba.FrameStatus.Complete:
			image = frame.as_opencv_image()
			datetime = self._datetime(frame)
			self._result_lock.acquire()
			self._result = CameraResult(image=image, datetime=datetime)
			self._result_event.set()
			self._result_lock.release()
		cam.queue_frame(frame)
	
	async def _run(self):
		with self.ctx:
			with self.cam:
				self.cam.start_streaming(self._frame_handler)
				await self._stop_event.wait()
	
	async def start(self):
		self._loop.create_task(self._run())
	
	async def stop(self):
		self._stop_event.set()
	
	async def read(self):
		await self._loop.run_in_executor(self._pool, self._result_event.wait, self.timeout)
		if not self._result_event.is_set():
			raise CameraException("VimbaCamera failed")
		await self._loop.run_in_executor(self._pool, self._result_lock.acquire)
		res = self._result
		self._result_event.clear()
		self._result_lock.release()
		return res
	
	def save_params(self, fn):
		with self.ctx:
			with self.cam:
				self.cam.save_settings(fn, vimba.PersistType.NoLUT)
	
	def _close(self):
		self._stop_event.set()
	
	def load_params(self, fn):
		# One time isn't enough to load the LineSelector settings ¯\_(ツ)_/¯
		with self.ctx:
			with self.cam:
				self.cam.load_settings(fn, vimba.PersistType.NoLUT)
		with self.ctx:
			with self.cam:
				self.cam.load_settings(fn, vimba.PersistType.NoLUT)
