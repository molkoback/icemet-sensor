import aiohttp
import certifi

import asyncio
import logging
import ssl
import time

class Status:
	def __init__(self, ctx, **kwargs):
		self.ctx = ctx
		self.delay = kwargs.get("delay", 10 * 60)
		self._ssl_ctx = None
	
	async def _create_ssl_context(self, session):
		ssl_ctx = ssl.create_default_context(cafile=certifi.where())
		try:
			await session.post(self.ctx.cfg.status.url, ssl=ssl_ctx)
			self._ssl_ctx = ctx
		except:
			self._ssl_ctx = False
	
	async def _send(self):
		async with aiohttp.ClientSession() as session:
			if self._ssl_ctx is None:
				await self._create_ssl_context(session)
			
			auth = aiohttp.BasicAuth(self.ctx.cfg.status.user, self.ctx.cfg.status.passwd)
			form = {
				"type": self.ctx.cfg.sensor.type,
				"id": self.ctx.cfg.sensor.id,
				"location": self.ctx.cfg.meas.location,
				"time": time.time()
			}
			async with session.post(self.ctx.cfg.status.url, auth=auth, data=form, ssl=self._ssl_ctx) as resp:
				delay = (await resp.json())["delay"]
				logging.debug("Status message sent ({:.2f} s)".format(delay))
	
	async def run(self):
		try:
			last = 0
			while not self.ctx.quit.is_set():
				await asyncio.sleep(1.0)
				if time.time() - last >= self.delay:
					try:
						await self._send()
						last = time.time()
					except:
						logging.error("Failed status message")
		except KeyboardInterrupt:
			self.ctx.quit.set()
