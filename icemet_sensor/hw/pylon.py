from icemet_sensor.camera import CameraResult, Camera, CameraException

from pypylon import pylon

import time

class PylonCamera(Camera):
	def __init__(self, params=None):
		try:
			self.cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
		except:
			raise CameraException("PylonCamera not found")
		
		if params:
			self.load_params(params)
		
		self.converter = pylon.ImageFormatConverter()
		self.converter.OutputPixelFormat = pylon.PixelType_Mono8
		self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
	
	def start(self):
		self.cam.Open()
		self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
	
	def stop(self):
		self.cam.StopGrabbing()
		self.cam.Close()
	
	def read(self):
		res = self.cam.RetrieveResult(1000, pylon.TimeoutHandling_ThrowException)
		if res.GrabSucceeded():
			image = self.converter.Convert(res).GetArray()
			stamp = time.time()
			return CameraResult(image=image, time=stamp)
	
	def save_params(self, fn):
		self.cam.Open()
		pylon.FeaturePersistence.Save(fn, self.cam.GetNodeMap())
		self.cam.Close()
	
	def load_params(self, fn):
		self.cam.Open()
		pylon.FeaturePersistence.Load(fn, self.cam.GetNodeMap(), True)
		self.cam.Close()
