import asyncio
import datetime
import os

version = "2.1.0-dev"
homedir = os.path.join(os.path.expanduser("~"), ".icemet")
datadir =  os.path.join(os.path.dirname(__file__), "data")

class Context:
	def __init__(self):
		self.cfg = None
		self.args = None
		self.loop = asyncio.get_event_loop()
		self.quit = asyncio.Event()
