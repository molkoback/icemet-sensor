from icemet.file import File

import aioftp

import asyncio
import concurrent.futures
from ftplib import FTP
import logging
import os
import time

class Sender:
	def __init__(self, ctx):
		self.ctx = ctx
		self._client = aioftp.Client()
		self._pool = concurrent.futures.ThreadPoolExecutor()
	
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
	
	def _find_files(self):
		files = []
		for fn in os.listdir(self.ctx.cfg.save.dir):
			path = os.path.join(self.ctx.cfg.save.dir, fn)
			if os.path.isfile(path):
				try:
					files.append((File.frompath(fn), path))
				except:
					pass
		files.sort(key=lambda t: t[0])
		return files
	
	async def _cycle(self):
		files = await self.ctx.loop.run_in_executor(self._pool, self._find_files)
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
		
		for f, path_src in files:
			if self.ctx.quit.is_set():
				break
			
			t = time.time()
			path_dst = self.ctx.cfg.ftp.dir + "/" + os.path.basename(path_src)
			try:
				await self._client.upload(path_src, self.ctx.cfg.ftp.tmp, write_into=True)
				await self._client.rename(self.ctx.cfg.ftp.tmp, path_dst)
			except:
				logging.error("Upload failed")
				await asyncio.sleep(1.0)
				return
			
			await self.ctx.loop.run_in_executor(self._pool, os.remove, path_src)
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
