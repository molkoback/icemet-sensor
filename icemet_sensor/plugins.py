import importlib
import logging
import sys

class PluginContainer:
	def __init__(self, plugins_path):
		sys.path.append(plugins_path)
		self._plugins = {}
	
	def load(self, name):
		module = importlib.import_module(name)
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
