from icemet_sensor.util import datetime_utc

import cv2
import numpy as np

import asyncio
import os
import random

class CameraException(Exception):
	pass

class CameraResult:
	def __init__(self, **kwargs):
		self.image = kwargs.get("image", None)
		self.datetime = kwargs.get("datetime", None)

class Camera:
	async def start(self) -> None:
		raise NotImplementedError()
	
	async def stop(self) -> None:
		raise NotImplementedError()
	
	async def read(self) -> CameraResult:
		raise NotImplementedError()
	
	def save_params(self, fn: str) -> None:
		raise NotImplementedError()
	
	def load_params(self, fn: str) -> None:
		raise NotImplementedError()
	
	def _close(self) -> None:
		raise NotImplementedError()
	
	def close(self):
		try:
			self._close()
		except NotImplementedError:
			pass
		except:
			logging.debug("Failed to close Camera")

class DummyCamera(Camera):
	def __init__(self, size=(640, 480), low=0, high=255):
		self.size = size
		self.low = low
		self.high = high
	
	async def start(self):
		pass
	
	async def stop(self):
		pass
	
	async def read(self):
		await asyncio.sleep(random.randint(1, 50)/1000)
		return CameraResult(
			image=np.random.randint(
				self.low, high=self.high,
				size=(self.size[1], self.size[0]),
				dtype=np.uint8
			),
			datetime=datetime_utc()
		)

class ImageReaderCamera(Camera):
	def __init__(self, dir=".", fps=1.0):
		self.dir = dir
		self.fps = fps
		self._files = [os.path.join(dir, file) for file in os.listdir(dir)]
		self._files.sort()
	
	async def start(self):
		pass
	
	async def stop(self):
		pass
	
	async def read(self):
		await asyncio.sleep(1/self.fps)
		if not self._files:
			raise CameraException("Out of images")
		img = cv2.imread(self._files.pop(0), cv2.IMREAD_GRAYSCALE)
		return CameraResult(
			image=img,
			datetime=datetime_utc()
		)

cameras = {
	"dummy": DummyCamera,
	"image_reader": ImageReaderCamera
}
try:
	from icemet_sensor.hw.spin import SpinCamera, SpinCameraSingle
	cameras["spin"] = SpinCamera
	cameras["spin_single"] = SpinCameraSingle
except:
	pass
try:
	from icemet_sensor.hw.pylon import PylonCamera
	cameras["pylon"] = PylonCamera
except:
	pass
try:
	from icemet_sensor.hw.vimba import VimbaCamera
	cameras["vimba"] = VimbaCamera
except:
	pass

def create_camera(name, **kwargs):
	if not name in cameras:
		raise CameraException("Camera not installed '{}'".format(name))
	return cameras[name](**kwargs)
