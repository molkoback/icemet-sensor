from icemet_sensor.camera import CameraResult, Camera, CameraException

from pypylon import pylon

import asyncio
import concurrent.futures
import time

class PylonCamera(Camera):
	def __init__(self, params=None):
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
	
	async def start(self):
		self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
	
	async def stop(self):
		self.cam.StopGrabbing()
	
	def _read(self):
		res = self.cam.RetrieveResult(1000, pylon.TimeoutHandling_ThrowException)
		stamp = time.time()
		image = self.converter.Convert(res).GetArray()
		return CameraResult(image=image, time=stamp)
	
	async def read(self):
		return await self._loop.run_in_executor(self._pool, self._read)
	
	def save_params(self, fn):
		pylon.FeaturePersistence.Save(fn, self.cam.GetNodeMap())
	
	def load_params(self, fn):
		pylon.FeaturePersistence.Load(fn, self.cam.GetNodeMap(), True)
	
	def close(self):
		self.cam.Close()
