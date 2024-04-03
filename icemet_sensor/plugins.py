import importlib
import logging
import os

class PluginContainer:
	def __init__(self, plugins_path):
		self.plugins_path = plugins_path
		self._plugins = {}
	
	def load(self, name):
		path = os.path.join(self.plugins_path, name+".py")
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
		
		logging.debug("Plugin '{}' with {} hooks".format(name, count))
	
	async def call(self, name, *args, **kwargs):
		for func in self._plugins.get(name, []):
			await func(*args, **kwargs)
