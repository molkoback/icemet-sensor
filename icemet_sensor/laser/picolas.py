from icemet_sensor.laser import Laser, LaserException

import serial

import time

_default_on_params = [
	"laseroff",
	"default",
	"strgmode 0",
	"svoltage 15000",
	"spulse 50",
	"socur 3000",
	"sshots 1",
	"sreprate 1",
	"smode 1",
	"stempoff 80",
	"laseron"
]

_default_off_params = [
	"laseroff"
]

class PicoLAS(Laser):
	def __init__(self, **kwargs):
		self.on_params = kwargs.get("on_params", _default_on_params)
		self.off_params = kwargs.get("off_params", _default_off_params)
		
		self._delay = 0.010
		
		self._ser = serial.Serial()
		self._ser.port = kwargs.get("port", "COM3")
		self._ser.baudrate = 115200
		self._ser.bytesize = serial.EIGHTBITS
		self._ser.parity = serial.PARITY_EVEN
		self._ser.stopbits = serial.STOPBITS_ONE
		self._ser.timeout = 1.0
	
	def _open(self):
		try:
			self._ser.open()
			ret, _ = self._write("gvoltage")
			if not ret:
				self._ser.close()
				raise Exception()
		except:
			raise LaserException("Couldn't connect to PicoLAS at '{}'".format(self._ser.port))
	
	def _close(self):
		self._ser.close()
	
	def _write(self, cmd):
		data = ("%s\r" % cmd).encode("utf-8")
		self._ser.write(data)
		resp = self._ser.read_until(b"\r\n\n")
		lines = resp.decode("utf-8").rstrip().split("\r\n")
		return lines[-1] == "0", lines[:1]
	
	def _write_params(self, params):
		self._open()
		for param in params:
			ret, _ = self._write(param)
			if not ret:
				raise LaserException("Failed PicoLAS parameter '{}'".format(param))
			time.sleep(self._delay)
		self._close()
	
	def on(self):
		self._write_params(self.on_params)
	
	def off(self):
		self._write_params(self.off_params)
