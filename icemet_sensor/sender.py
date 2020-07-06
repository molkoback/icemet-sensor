from icemet.file import File

import aioftp

import asyncio
import concurrent.futures
from ftplib import FTP
import logging
import os
import time

def _find_files(dir):
	files = []
	for fn in os.listdir(dir):
		path = os.path.join(dir, fn)
		if os.path.isfile(path):
			try:
				files.append(File.frompath(fn))
			except:
				pass
	files.sort()
	return files

class Sender:
	def __init__(self, cfg):
		self.cfg = cfg
		self.loop = asyncio.get_event_loop()
		self._client = aioftp.Client()
	
	async def _connect(self):
		await self._client.connect(self.cfg.ftp.host, port=self.cfg.ftp.port)
		await self._client.login(self.cfg.ftp.user, self.cfg.ftp.passwd)
		logging.debug("Connected")
	
	async def _reconnect(self, n):
		for i in range(1, n+1):
			try:
				logging.debug("Reconnect attempt {}/{}".format(i, n))
				await self._connect()
			except:
				await asyncio.sleep(60)
	
	async def _find_files(self):
		with concurrent.futures.ProcessPoolExecutor() as pool:
			files = await self.loop.run_in_executor(pool, _find_files, self.cfg.save.dir)
		return files
	
	async def _send(self, fn_in, fn_out):
		async with aioftp.ClientSession(
			self.cfg.ftp.host, self.cfg.ftp.port,
			self.cfg.ftp.user, self.cfg.ftp.passwd
		) as client:
			await client.upload(fn_in, fn_out, write_into=True)
	
	async def _cycle(self):
		files = await self._find_files()
		for f in files:
			t = time.time()
			fn_in = f.path(root=self.cfg.save.dir, ext=self.cfg.save.type, subdirs=False)
			fn_out = f.path(root=self.cfg.ftp.path, ext=self.cfg.save.type, subdirs=False)
			try:
				await self._send(fn_in, fn_out)
			except:
				self._reconnect(3)
				break
			os.remove(fn_in)
			logging.debug("Sent {} ({:.2f} s)".format(f.name, time.time()-t))
	
	async def run(self):
		logging.info("FTP server {}:{}".format(self.cfg.ftp.host, self.cfg.ftp.port))
		await self._connect()
		while True:
			await self._cycle()
			await asyncio.sleep(1.0)
