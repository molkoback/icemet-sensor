import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

version = "3.0.0.dev"
home_path = os.path.join(os.path.expanduser("~"), ".icemet")
data_path =  os.path.join(os.path.dirname(__file__), "data")
plugins_path = os.path.join(os.path.dirname(__file__), "plugins")

class Context:
	def __init__(self, args, cfg, plugins):
		self.args = args
		self.cfg = cfg
		self.plugins = plugins
		self.loop = asyncio.get_event_loop()
		self.pool = ThreadPoolExecutor()
		self.quit = asyncio.Event()
		self._vars = {}
		self._lock = asyncio.Lock()
	
	async def get(self, key, default=None):
		async with self._lock:
			val = self._vars.get(key, default)
		return val
	
	async def set(self, key, val):
		async with self._lock:
			self._vars[key] = val
