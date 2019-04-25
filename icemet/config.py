import os
import yaml

class ConfigException(Exception):
	pass

class Config:
	def __init__(self, fn):
		try:
			with open(fn, "r") as fp:
				d = yaml.load(fp, Loader=yaml.Loader)
			self.save = type("SaveParam", (object,), {
				"path": os.path.expanduser(os.path.normpath(d["save_path"])),
				"type": d["save_type"],
				"tmp": None
			})
			self.save.tmp = os.path.join(self.save.path, "tmp." + self.save.type)
			self.sensor = type("SensorParam", (object,), {
				"id": d["sensor_id"],
				"restart": d["sensor_restart"]
			})
			self.camera = type("SensorParam", (object,), {
				"id": d["camera_id"],
			})
			self.laser = type("SensorParam", (object,), {
				"port": d["laser_port"],
			})
			self.ftp = type("FTPParam", (object,), {
				"host": d["ftp_host"],
				"port": int(d["ftp_port"]),
				"user": d["ftp_user"],
				"passwd": d["ftp_passwd"],
				"path": d["ftp_path"]
			})
			self.meas = type("MeasureParam", (object,), {
				"delay": 1.0 / d["measure_fps"],
				"len": d["measure_len"],
				"n": float("inf")
			})
		except:
			raise ConfigException("Couldn't parse config file '%s'" % fn)
