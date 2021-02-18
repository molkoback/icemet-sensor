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
	
	async def _connected(self):
		try:
			await self._client.command("NOOP")
			return (await self._client.parse_line())[0] == "200"
		except:
			return False
	
	async def _connect(self):
		await self._client.connect(self.ctx.cfg.ftp.host, port=self.ctx.cfg.ftp.port)
		await self._client.login(self.ctx.cfg.ftp.user, self.ctx.cfg.ftp.passwd)
		logging.debug("Connected")
	
	async def _cycle(self):
		files = await self.ctx.loop.run_in_executor(self._pool, _find_files, self.ctx.cfg.save.dir)
		if not files:
			await asyncio.sleep(1.0)
			return
		
		if not await self._connected():
			try:
				await self._connect()
			except:
				logging.error("FTP server offline")
				await asyncio.sleep(1.0)
				return
		
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
				logging.error("Upload failed")
				await asyncio.sleep(1.0)
				return
			
			await self.ctx.loop.run_in_executor(None, os.remove, fn_in)
			logging.debug("Sent {} ({:.2f} s)".format(f.name(), time.time()-t))
	
	async def run(self):
		try:
			logging.info("FTP server {}:{}".format(self.ctx.cfg.ftp.host, self.ctx.cfg.ftp.port))
			while not self.ctx.quit.is_set():
				await self._cycle()
		except KeyboardInterrupt:
			self.ctx.quit.set()
		except Exception as e:
			logging.error(str(e))
			self.ctx.quit.set()
		finally:
			self._client.close()
