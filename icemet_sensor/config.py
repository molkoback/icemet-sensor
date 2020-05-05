from icemet_sensor import homedir, datadir

from icemet.cfg import Config, ConfigException

import os

default_file = os.path.join(homedir, "icemet-sensor.yaml")

def create_default_file():
	fn = os.path.join(datadir, "icemet-sensor.yaml")
	with open(fn) as fp:
		txt = fp.read()
	os.makedirs(homedir, exist_ok=True)
	with open(default_file, "w") as fp:
		fp.write(txt)

class SensorConfig(Config):
	def __init__(self, fn):
		try:
			self.read(fn)
			self.setDict(self.dict)
		except Exception as e:
			raise ConfigException("Couldn't parse config file '{}'\n{}".format(fn, e))
	
	def setDict(self, dict):
		self.save = type("SaveParam", (object,), {
			"dir": os.path.expanduser(os.path.normpath(dict["save"]["dir"])),
			"type": dict["save"]["type"],
			"tmp": None
		})
		self.save.tmp = os.path.join(self.save.dir, "tmp." + self.save.type)
		self.meas = type("MeasureParam", (object,), {
			"burst_delay": 1.0 / dict["measurement"]["burst_fps"],
			"burst_len": dict["measurement"]["burst_len"],
			"wait": dict["measurement"]["wait"],
			"n": float("inf")
		})
		self.sensor = type("SensorParam", (object,), {
			"id": dict["sensor"]["id"],
			"restart": dict["sensor"]["restart"]
		})
		self.camera = self._cfg_obj(dict["camera"], "CameraParam")
		self.laser = self._cfg_obj(dict["laser"], "LaserParam")
		self.ftp = type("FTPParam", (object,), {
			"host": dict["ftp"]["host"],
			"port": int(dict["ftp"]["port"]),
			"user": dict["ftp"]["user"],
			"passwd": dict["ftp"]["passwd"],
			"path": os.path.normpath(dict["ftp"]["path"])
		})
		self.preproc = type("PreprocParam", (object,), {
			"enable": dict["preproc"]["enable"],
			"crop": type("CropParam", (object,), {
				"x": dict["preproc"]["crop"]["x"],
				"y": dict["preproc"]["crop"]["y"],
				"w": dict["preproc"]["crop"]["w"],
				"h": dict["preproc"]["crop"]["h"]
			}),
			"rotate": dict["preproc"]["rotate"],
			"empty": type("EmptyParam", (object,), {
				"th_original": dict["preproc"]["empty"]["th_original"],
				"th_preproc": dict["preproc"]["empty"]["th_preproc"]
			}),
			"bgsub_stack_len": dict["preproc"]["bgsub_stack_len"]
		})
	
	def _cfg_obj(self, obj, clsname):
		k = next(iter(obj))
		return type(clsname, (object,), {
			"name": k,
			"kwargs": obj[k]
		})
