from icemet_sensor.util import Url, tmpfile

from icemet.file import File

import aioftp
import aiohttp

import asyncio
import logging
import os
import time

class ProtocolException(Exception):
	pass

class Protocol:
	def __init__(self, url):
		self.url = url
	
	async def upload(self, file):
		raise NotImplementedError()

class FTP(Protocol):
	def __init__(self, url):
		super().__init__(url)
		self._client = None
	
	async def _connected(self):
		try:
			await self._client.command("NOOP")
			return (await self._client.parse_line())[0] == "200"
		except:
			return False
	
	async def _connect(self):
		if not await self._connected():
			self._client = aioftp.Client()
			port = self.url.port if self.url.port else 21
			await self._client.connect(self.url.host, port=port)
			await self._client.login(self.url.user, self.url.password)
	
	async def upload(self, path):
		await self._connect()
		
		file = os.path.basename(path)
		dir = self.url.path
		dir = dir if dir.endswith("/") else dir+"/"
		tmp = dir + tmpfile() + os.path.splitext(file)[1]
		dst = dir + file
		
		await self._client.upload(path, tmp, write_into=True)
		await self._client.rename(tmp, dst)

class HTTP(Protocol):
	def __init__(self, url):
		super().__init__(url)
	
	async def upload(self, file):
		async with aiohttp.ClientSession() as session:
			auth = aiohttp.BasicAuth(self.url.user, self.url.password)
			with open(file, "rb") as fp:
				data = {"file": fp}
				async with session.post(self.url.join(hide_auth=True), auth=auth, data=data) as resp:
					if resp.status != 200:
						raise ProtocolException(resp.status)
					error = (await resp.json())["error"]
					if error:
						raise ProtocolException(error)

def create_protocol(url):
	url = Url(url)
	protocols = {
		"ftp": FTP,
		"https": HTTP,
		"http": HTTP
	}
	cls = protocols.get(url.scheme)
	if not cls:
		return None
	return cls(url)

class Uploader:
	def __init__(self, ctx):
		self.ctx = ctx
		self._proto = create_protocol(self.ctx.cfg["UPLOAD_URL"])
	
	def _find_files(self):
		files = []
		for fn in os.listdir(self.ctx.cfg["SAVE_PATH"]):
			path = os.path.join(self.ctx.cfg["SAVE_PATH"], fn)
			if os.path.isfile(path):
				try:
					files.append((File.frompath(fn), path))
				except:
					pass
		files.sort(key=lambda t: t[0])
		return files
	
	async def _cycle(self):
		files = await self.ctx.loop.run_in_executor(self.ctx.pool, self._find_files)
		if not files:
			await asyncio.sleep(1.0)
			return
		
		for f, path in files:
			if self.ctx.quit.is_set():
				break
			
			t = time.time()
			try:
				timeout = self.ctx.cfg.get("UPLOAD_TIMEOUT", 0)
				if timeout > 0:
					await asyncio.wait_for(self._proto.upload(path), timeout)
				else:
					await self._proto.upload(path)
				os.remove(path)
			except:
				logging.error("Upload failed")
				await asyncio.sleep(1.0)
				return
			logging.debug("Sent {} ({:.2f} s)".format(f.name(), time.time()-t))
	
	async def run(self):
		logging.info("Upload {}".format(self._proto.url.join(hide_auth=True)))
		try:
			while not self.ctx.quit.is_set():
				await self._cycle()
		except KeyboardInterrupt:
			pass
		except Exception as e:
			logging.error(str(e))
		self.ctx.quit.set()
