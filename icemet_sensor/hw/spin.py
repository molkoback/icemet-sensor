from icemet_sensor.camera import CameraResult, Camera, CameraException

import numpy as np
import PySpin

import time

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
	def __init__(self, id=0, params=None):
		self.system = None
		self.cam_list = None
		self.cam = None
		
		self.system = PySpin.System.GetInstance()
		self.cam_list = self.system.GetCameras()
		if id < self.cam_list.GetSize():
			self.cam = self.cam_list.GetByIndex(id)
		else:
			raise CameraException("SpinCamera not found '{}'".format(id))
		self.cam.Init()
		
		if params:
			self.load_params(params)
		self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
		
		self._start_time = None
		self._start_stamp = None
	
	async def start(self):
		self.cam.BeginAcquisition()
		self._start_stamp = self.cam.GetNextImage().GetTimeStamp()
		self._start_time = time.time()
	
	async def stop(self):
		self.cam.EndAcquisition()
	
	async def read(self):
		res = self.cam.GetNextImage()
		image = np.reshape(res.GetData(), (res.GetHeight(), res.GetWidth())).copy()
		stamp = (res.GetTimeStamp() - self._start_stamp) / 10**9 + self._start_time
		return CameraResult(image=image, time=stamp)
	
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
					params.append(param)
	
	def _get_params(self):
		params = []
		self._traverse(self.cam.GetNodeMap().GetNode("Root"), params)
		return params
	
	def save_params(self, fn):
		obj = {}
		for param in self._get_params():
			obj[param.name] = param.val()
		with open(fn, "w") as fp:
			json.dump(obj, fp, sort_keys=True, indent=4)
	
	def load_params(self, fn):
		with open(fn) as fp:
			obj = json.load(fp)
		params = self._get_params()
		for name, val in obj.items():
			for param in params:
				if name == param.name:
					param.set(val)
					break
	
	def __del__(self):
		if not self.cam is None:
			if self.cam.IsStreaming():
				self.cam.EndAcquisition()
			if self.cam.IsInitialized():
				self.cam.DeInit()
			del self.cam
		if not self.cam_list is None:
			self.cam_list.Clear()
		if not self.system is None:
			self.system.ReleaseInstance()
