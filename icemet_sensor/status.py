import aiohttp

import asyncio
import logging
import time

class Status:
	def __init__(self, ctx, **kwargs):
		self.ctx = ctx
		self.delay = kwargs.get("delay", 10 * 60)
	
	async def _send(self):
		async with aiohttp.ClientSession() as session:
			# Login
			auth = aiohttp.BasicAuth(self.ctx.cfg.status.user, self.ctx.cfg.status.passwd)
			await session.post(self.ctx.cfg.status.url, auth=auth)
			
			# Send message
			form = {
				"id": self.ctx.cfg.sensor.id,
				"name": self.ctx.cfg.sensor.name,
				"time": time.time()
			}
			async with session.post(self.ctx.cfg.status.url, data=form) as resp:
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
