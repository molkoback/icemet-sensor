import importlib.util
import os

class PluginContainer:
	def __init__(self, plugins_paths):
		self._plugins_available = {}
		for path in plugins_paths:
			for file in os.listdir(path):
				name, ext = os.path.splitext(file)
				if ext == ".py" and not name in self._plugins_available:
					self._plugins_available[name] = os.path.join(path, file)
		
		self._plugins = {}
	
	def plugins_available(self):
		return list(self._plugins_available.keys())
	
	def load(self, name):
		path = self._plugins_available[name]
		spec = importlib.util.spec_from_file_location(name, path)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		
		count = 0
		for func_name in dir(module):
			if func_name.startswith("on_"):
				count += 1
				if not func_name in self._plugins:
					self._plugins[func_name] = []
				self._plugins[func_name].append(getattr(module, func_name))
		
		return count
	
	async def call(self, name, *args, **kwargs):
		for func in self._plugins.get(name, []):
			await func(*args, **kwargs)
