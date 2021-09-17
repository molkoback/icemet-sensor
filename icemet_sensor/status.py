from icemet_sensor.util import Url

import aiohttp

import asyncio
import logging
import ssl
import time

class Status:
	def __init__(self, ctx, **kwargs):
		self.ctx = ctx
		self.delay = kwargs.get("delay", 10 * 60)
		self._url = Url(self.ctx.cfg.status.url)
	
	async def _send(self):
		async with aiohttp.ClientSession() as session:
			auth = aiohttp.BasicAuth(self._url.user, self._url.password)
			form = {
				"type": self.ctx.cfg.sensor.type,
				"id": self.ctx.cfg.sensor.id,
				"location": self.ctx.cfg.meas.location,
				"time": time.time()
			}
			async with session.post(self._url.join(hide_auth=True), auth=auth, data=form) as resp:
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
