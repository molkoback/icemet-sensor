from icemet.cfg import Config, ConfigException

import os

default_file = os.path.join(os.path.expanduser("~"), ".icemet-sensor.yaml")

class SensorConfig(Config):
	def __init__(self, fn):
		try:
			self.read(fn)
			self.save = type("SaveParam", (object,), {
				"path": os.path.expanduser(os.path.normpath(self.d["save_path"])),
				"type": self.d["save_type"],
				"tmp": None
			})
			self.save.tmp = os.path.join(self.save.path, "tmp." + self.save.type)
			self.sensor = type("SensorParam", (object,), {
				"id": self.d["sensor_id"],
				"restart": self.d["sensor_restart"]
			})
			self.camera = type("SensorParam", (object,), {
				"type": self.d["camera_type"],
				"kwargs": self.d["camera_args"]
			})
			self.laser = type("SensorParam", (object,), {
				"type": self.d["laser_type"],
				"kwargs": self.d["laser_args"]
			})
			self.ftp = type("FTPParam", (object,), {
				"host": self.d["ftp_host"],
				"port": int(self.d["ftp_port"]),
				"user": self.d["ftp_user"],
				"passwd": self.d["ftp_passwd"],
				"path": os.path.normpath(self.d["ftp_path"])
			})
			self.meas = type("MeasureParam", (object,), {
				"delay": 1.0 / self.d["measure_fps"],
				"len": self.d["measure_len"],
				"n": float("inf")
			})
		except:
			raise ConfigException("Couldn't parse config file '{}'".format(fn))
