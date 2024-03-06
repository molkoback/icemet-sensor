import asyncio
import concurrent
import datetime
import os

version = "3.0.0-dev"
homedir = os.path.join(os.path.expanduser("~"), ".icemet")
datadir =  os.path.join(os.path.dirname(__file__), "data")

class Context:
	def __init__(self):
		self.cfg = None
		self.args = None
		self.loop = asyncio.get_event_loop()
		self.pool = concurrent.futures.ThreadPoolExecutor()
		self.quit = asyncio.Event()
