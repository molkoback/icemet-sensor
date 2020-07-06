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
			"type": dict["save"]["type"],
			"is_pkg": False,
			"ext": None,
			"tmp": None
		})
		ext = name2ext(self.save.type)
		self.save.is_pkg = bool(ext)
		self.save.ext = ext if ext else "."+self.save.type
		self.save.tmp = os.path.join(self.save.dir, "tmp" + self.save.ext)
		self.meas = type("MeasureParam", (object,), {
			"burst_fps": float(dict["measurement"]["burst_fps"]),
			"burst_delay": 1.0 / float(dict["measurement"]["burst_fps"]),
			"burst_len": int(dict["measurement"]["burst_len"]),
			"wait": float(dict["measurement"]["wait"]),
		})
		self.sensor = type("SensorParam", (object,), {
			"id": int(dict["sensor"]["id"], 16)
		})
		self.camera = self._cfg_obj(dict["camera"], "CameraParam")
		self.laser = self._cfg_obj(dict["laser"], "LaserParam")
		self.ftp = type("FTPParam", (object,), {
			"enable": dict["ftp"]["enable"],
			"host": dict["ftp"]["host"],
			"port": int(dict["ftp"]["port"]),
			"user": dict["ftp"]["user"],
			"passwd": dict["ftp"]["passwd"],
			"path": os.path.normpath(dict["ftp"]["path"])
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
			"empty": type("EmptyParam", (object,), {
				"th_original": int(dict["preproc"]["empty"]["th_original"]),
				"th_preproc": int(dict["preproc"]["empty"]["th_preproc"])
			}),
			"bgsub_stack_len": int(dict["preproc"]["bgsub_stack_len"])
		})
	
	def _cfg_obj(self, obj, clsname):
		k = next(iter(obj))
		return type(clsname, (object,), {
			"name": k,
			"kwargs": obj[k]
		})
