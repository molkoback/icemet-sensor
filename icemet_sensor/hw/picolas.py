from icemet_sensor.laser import Laser, LaserException

import serial

import asyncio
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
		
		self._ser = None
		self._ser = serial.Serial()
		self._ser.port = kwargs.get("port", "COM3")
		self._ser.baudrate = 115200
		self._ser.bytesize = serial.EIGHTBITS
		self._ser.parity = serial.PARITY_EVEN
		self._ser.stopbits = serial.STOPBITS_ONE
		self._ser.timeout = 1.0
	
	async def _open(self):
		try:
			self._ser.open()
			if not await self._write("gvoltage"):
				raise Exception()
		except:
			self._ser.close()
			raise LaserException("Couldn't connect to PicoLAS at '{}'".format(self._ser.port))
	
	async def _write(self, cmd):
		data = ("{}\r".format(cmd)).encode("utf-8")
		self._ser.write(data)
		
		t = time.time()
		while not self._ser.in_waiting:
			if time.time() - t > self._ser.timeout:
				raise LaserException("PicoLAS did not respond")
			await asyncio.sleep(0.010)
		
		resp = self._ser.read_until(b"\r\n\n")
		lines = resp.decode("utf-8").rstrip().split("\r\n")
		return lines[-1] == "0"
	
	async def _write_params(self, params):
		await self._open()
		for param in params:
			if not await self._write(param):
				raise LaserException("Failed PicoLAS parameter '{}'".format(param))
			await asyncio.sleep(0.010)
		self._ser.close()
	
	async def on(self):
		await self._write_params(self.on_params)
	
	async def off(self):
		await self._write_params(self.off_params)
	
	def _close(self):
		if not self._ser is None:
			self._ser.close()
