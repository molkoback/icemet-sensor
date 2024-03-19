from icemet_sensor.camera import cameras, CameraResult, Camera, CameraException
from icemet_sensor.util import datetime_utc

import numpy as np
import PySpin

import asyncio
import atexit
import collections
import concurrent.futures
import json
import logging
import time

_system = PySpin.System.GetInstance()
_cam_list = _system.GetCameras()
_lock = asyncio.Lock()

def _atexit():
	_cam_list.Clear()
	_system.ReleaseInstance()
atexit.register(_atexit)

class SpinParameter:
	def __init__(self, node):
		self.node = node
		self.type = self.node.GetPrincipalInterfaceType()
	
	@property
	def name(self):
		return PySpin.CValuePtr(self.node).GetDisplayName()
	
	def val(self):
		if self.type == PySpin.intfIString:
			return PySpin.CStringPtr(self.node).GetValue()
		elif self.type == PySpin.intfIInteger:
			return PySpin.CIntegerPtr(self.node).GetValue()
		elif self.type == PySpin.intfIFloat:
			return PySpin.CFloatPtr(self.node).GetValue()
		elif self.type == PySpin.intfIBoolean:
			return PySpin.CBooleanPtr(self.node).GetValue()
		elif self.type == PySpin.intfIEnumeration:
			return PySpin.CEnumerationPtr(self.node).GetIntValue()
		return None
	
	def set(self, val):
		if self.type == PySpin.intfIString:
			PySpin.CStringPtr(self.node).SetValue(val)
		elif self.type == PySpin.intfIInteger:
			PySpin.CIntegerPtr(self.node).SetValue(val)
		elif self.type == PySpin.intfIFloat:
			PySpin.CFloatPtr(self.node).SetValue(val)
		elif self.type == PySpin.intfIBoolean:
			PySpin.CBooleanPtr(self.node).SetValue(val)
		elif self.type == PySpin.intfIEnumeration:
			PySpin.CEnumerationPtr(self.node).SetIntValue(val)

class SpinCamera(Camera):
	def __init__(self, serial=None, params=None, hwclock=True, timeout=1.0):
		self.cam = None
		
		if serial is None:
			self.cam = _cam_list.GetByIndex(0)
		else:
			self.cam = _cam_list.GetBySerial(serial)
		self.cam.Init()
		
		if params:
			self.load_params(params)
		self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
		
		self._loop = asyncio.get_event_loop()
		self._pool = concurrent.futures.ThreadPoolExecutor()
		
		self.hwclock = hwclock
		self.timeout = timeout
		self._start_time = None
		self._start_stamp = None
	
	async def start(self):
		if not self.cam.IsStreaming():
			self.cam.BeginAcquisition()
	
	async def stop(self):
		if self.cam.IsStreaming():
			self.cam.EndAcquisition()
	
	def _datetime(self, res):
		if not self.hwclock:
			return datetime_utc()
		
		stamp = res.GetTimeStamp()
		if self._start_stamp is None or stamp < self._start_stamp:
			self._start_stamp = stamp
			self._start_time = time.time()
			return datetime_utc()
		
		_time = (stamp - self._start_stamp) / 10**9 + self._start_time
		return datetime_utc(_time)
	
	def _read(self):
		try:
			res = self.cam.GetNextImage(int(self.timeout * 1000))
			datetime = self._datetime(res)
			image = np.reshape(res.GetData(), (res.GetHeight(), res.GetWidth())).copy()
			return CameraResult(image=image, datetime=datetime)
		except:
			return None
	
	async def read(self):
		res = await self._loop.run_in_executor(self._pool, self._read)
		if res is None:
			raise CameraException("SpinCamera failed")
		return res
	
	def _traverse(self, node, params):
		category = PySpin.CCategoryPtr(node)
		for child in category.GetFeatures():
			if not PySpin.IsAvailable(child) or not PySpin.IsReadable(child):
				continue
			if child.GetPrincipalInterfaceType() == PySpin.intfICategory:
				self._traverse(child, params)
			else:
				param = SpinParameter(child)
				if not param.val() is None and PySpin.IsWritable(child):
					params[param.name] = param
	
	def _get_params(self):
		params = {}
		self._traverse(self.cam.GetNodeMap().GetNode("Root"), params)
		return params
	
	def save_params(self, fn):
		obj = {}
		for name, param in self._get_params().items():
			obj[name] = param.val()
		with open(fn, "w") as fp:
			json.dump(obj, fp, indent=4)
	
	def load_params(self, fn):
		with open(fn) as fp:
			obj = json.load(fp, object_pairs_hook=collections.OrderedDict)
		
		for name, val in obj.items():
			params = self._get_params()
			try:
				params[name].set(val)
			except:
				raise CameraException("Failed parameter '{}'".format(name))
	
	def _close(self):
		if not self.cam is None:
			if self.cam.IsStreaming():
				self.cam.EndAcquisition()
			if self.cam.IsInitialized():
				self.cam.DeInit()
			del self.cam

class SpinSingleCamera(SpinCamera):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)
	
	async def start(self):
		pass
	
	async def stop(self):
		pass
	
	def _read(self):
		try:
			self.cam.BeginAcquisition()
			res = self.cam.GetNextImage(int(self.timeout * 1000))
			datetime = self._datetime(res)
			self.cam.EndAcquisition()
			image = np.reshape(res.GetData(), (res.GetHeight(), res.GetWidth())).copy()
			return CameraResult(image=image, datetime=datetime)
		except:
			return None
	
	async def read(self):
		async with _lock:
			res = await self._loop.run_in_executor(self._pool, self._read)
		if res is None:
			raise CameraException("SpinCamera failed")
		return res

cameras["spin"] = SpinCamera
cameras["spin_single"] = SpinSingleCamera
