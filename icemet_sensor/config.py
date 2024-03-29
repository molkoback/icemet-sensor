from icemet_sensor import homedir, datadir

from icemet.cfg import Config, ConfigException
from icemet.pkg import name2ext

import os
import shutil

default_file = os.path.join(datadir, "icemet-sensor.yaml")

def create_config_file(dst):
	os.makedirs(os.path.split(dst)[0], exist_ok=True)
	shutil.copy(default_file, dst)

class SensorConfig(Config):
	def set_dict(self, dict):
		super().set_dict(dict)
		self.save = type("SaveParam", (object,), {
			"dir": os.path.expanduser(os.path.normpath(dict["save"]["dir"])),
			"type": self._createable(dict["save"]["type"]),
			"is_pkg": False,
			"ext": None,
			"tmp": None
		})
		ext = name2ext(self.save.type.name)
		self.save.is_pkg = bool(ext)
		self.save.ext = ext if ext else "."+self.save.type.name
		self.save.tmp = os.path.join(self.save.dir, "tmp" + self.save.ext)
		self.meas = type("MeasureParam", (object,), {
			"location": dict["measurement"]["location"],
			"burst_fps": float(dict["measurement"]["burst_fps"]),
			"burst_delay": 1.0 / float(dict["measurement"]["burst_fps"]),
			"burst_len": int(dict["measurement"]["burst_len"]),
			"wait": float(dict["measurement"]["wait"])
		})
		self.sensor = type("SensorParam", (object,), {
			"type": dict["sensor"]["type"],
			"id": int(dict["sensor"]["id"], 16),
			"timeout": float(dict["sensor"]["timeout"]),
			"black_th": float(dict["sensor"]["black_th"])
		})
		self.camera = self._createable(dict["camera"])
		self.laser = self._createable(dict["laser"])
		self.temp_relay = None
		if dict["temp_relay"]:
			self.temp_relay = self._createable(dict["temp_relay"])
		self.upload = type("UploadParam", (object,), {
			"url": dict["upload"]["url"],
			"timeout": dict["upload"]["timeout"]
		})
		self.status = type("StatusParam", (object,), {
			"url": dict["status"]["url"]
		})
		self.preproc = type("PreprocParam", (object,), {
			"enable": dict["preproc"]["enable"],
			"crop": type("CropParam", (object,), {
				"x": int(dict["preproc"]["crop"]["x"]),
				"y": int(dict["preproc"]["crop"]["y"]),
				"w": int(dict["preproc"]["crop"]["w"]),
				"h": int(dict["preproc"]["crop"]["h"])
			}),
			"rotate": float(dict["preproc"]["rotate"]),
			"empty_th": int(dict["preproc"]["empty_th"]),
			"bgsub_stack_len": int(dict["preproc"]["bgsub_stack_len"])
		})
	
	def _createable(self, obj):
		k = next(iter(obj))
		return type("Createable", (object,), {
			"name": k,
			"kwargs": obj[k]
		})
