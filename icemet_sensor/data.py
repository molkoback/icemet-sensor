import threading

def safe(func):
	def wrapper(self, *args, **kwargs):
		self.lock.acquire()
		ret = func(self, *args, **kwargs)
		self.lock.release()
		return ret
	return wrapper

class Safe:
	lock = threading.Lock()

class Stack(Safe):
	def __init__(self, size=float("inf")):
		self.size = size
		self.data = []
	
	@safe
	def push(self, obj):
		if len(self.data) >= self.size:
			self.data.pop(0)
		self.data.append(obj)
	
	@safe
	def pop(self):
		if len(self.data) == 0:
			return None
		return self.data.pop(-1)

class Atomic(Safe):
	def __init__(self, val=None):
		self.val = val
	
	@safe
	def set(self, val):
		self.val = val
	
	@safe
	def get(self):
		return self.val
