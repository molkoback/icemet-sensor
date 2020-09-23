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
	def __init__(self, ctx):
		self.ctx = ctx
		self._client = aioftp.Client()
		self._pool = concurrent.futures.ProcessPoolExecutor()
	
	async def _connect(self):
		await self._client.connect(self.ctx.cfg.ftp.host, port=self.ctx.cfg.ftp.port)
		await self._client.login(self.ctx.cfg.ftp.user, self.ctx.cfg.ftp.passwd)
		logging.debug("Connected")
	
	async def _reconnect(self, n):
		for i in range(1, n+1):
			try:
				logging.debug("Reconnect attempt {}/{}".format(i, n))
				await self._connect()
			except:
				await asyncio.sleep(60)
	
	async def _cycle(self):
		files = await self.ctx.loop.run_in_executor(self._pool, _find_files, self.ctx.cfg.save.dir)
		for f in files:
			if self.ctx.quit.is_set():
				break
			
			t = time.time()
			fn_in = f.path(root=self.ctx.cfg.save.dir, ext=self.ctx.cfg.save.ext, subdirs=False)
			fn_out = self.ctx.cfg.ftp.dir + "/" + f.path(root="", ext=self.ctx.cfg.save.ext, subdirs=False)
			try:
				await self._client.upload(fn_in, self.ctx.cfg.ftp.tmp, write_into=True)
				await self._client.rename(self.ctx.cfg.ftp.tmp, fn_out)
			except:
				await self._reconnect(3)
				break
			
			await self.ctx.loop.run_in_executor(None, os.remove, fn_in)
			logging.debug("Sent {} ({:.2f} s)".format(f.name(), time.time()-t))
		if not files:
			await asyncio.sleep(1.0)
	
	async def run(self):
		logging.info("FTP server {}:{}".format(self.ctx.cfg.ftp.host, self.ctx.cfg.ftp.port))
		try:
			await self._connect()
			while not self.ctx.quit.is_set():
				await self._cycle()
		except KeyboardInterrupt:
			self.ctx.quit.set()
