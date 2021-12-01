from icemet_sensor.camera import CameraResult, Camera, CameraException
from icemet_sensor.util import datetime_utc

from pypylon import pylon

import asyncio
import concurrent.futures

class PylonCamera(Camera):
	def __init__(self, params=None, timeout=1.0):
		try:
			self.cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
		except:
			raise CameraException("PylonCamera not found")
		self.cam.Open()
		
		if params:
			self.load_params(params)
		
		self.converter = pylon.ImageFormatConverter()
		self.converter.OutputPixelFormat = pylon.PixelType_Mono8
		self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
		self._loop = asyncio.get_event_loop()
		self._pool = concurrent.futures.ThreadPoolExecutor()
		
		self.timeout = timeout
	
	async def start(self):
		self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
	
	async def stop(self):
		self.cam.StopGrabbing()
	
	def _read(self):
		try:
			res = self.cam.RetrieveResult(int(self.timeout * 1000), pylon.TimeoutHandling_ThrowException)
			datetime = datetime_utc()
			image = self.converter.Convert(res).GetArray()
			return CameraResult(image=image, datetime=datetime)
		except:
			return None
	
	async def read(self):
		res = await self._loop.run_in_executor(self._pool, self._read)
		if res is None:
			raise CameraException("PylonCamera failed")
		return res
	
	def save_params(self, fn):
		pylon.FeaturePersistence.Save(fn, self.cam.GetNodeMap())
	
	def load_params(self, fn):
		pylon.FeaturePersistence.Load(fn, self.cam.GetNodeMap(), True)
	
	def _close(self):
		self.cam.Close()
