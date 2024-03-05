import asyncio
from datetime import datetime, timezone
import gc

class Url:
	def __init__(self, url):
		self.scheme, self.user, self.password, self.host, self.port, self.path = Url.parse(url)
	
	def join(self, hide_auth=False):
		if hide_auth or not self.user:
			auth = ""
		else:
			auth = self.user
			if self.password:
				auth += ":" + self.password
			auth += "@"
		if self.port:
			port = ":"+str(self.port)
		else:
			port = ""
		return "{}://{}{}{}{}".format(self.scheme, auth, self.host, port, self.path)
	
	@staticmethod
	def parse(url):
		scheme, tail = url.split("://", 1)
		if "@" in tail:
			head, tail = tail.split("@", 1)
			if ":" in head:
				user, password = head.split(":", 1)
			else:
				user, password = head, ""
		else:
			user, password = "", ""
		
		if "/" in tail:
			head, path = tail.split("/", 1)
			path = "/" + path
		else:
			head, path = tail, "/"
		
		if ":" in head:
			host, port = head.split(":", 1)
			port = int(port)
		else:
			host, port = head, None
		
		return scheme, user, password, host, port, path

def datetime_utc(timestamp=None):
	dt = datetime.utcnow() if timestamp is None else datetime.fromtimestamp(timestamp, timezone.utc)
	return dt.replace(tzinfo=None)

async def collect_garbage(quit, delay):
	try:
		while not quit.is_set():
			gc.collect(generation=2)
			await asyncio.sleep(delay)
	except KeyboardInterrupt:
		quit.set()
