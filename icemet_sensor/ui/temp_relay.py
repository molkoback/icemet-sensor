from icemet_sensor import home_path, plugins_path
from icemet_sensor.plugins import PluginContainer
from icemet_sensor.temp_relay import create_temp_relay

from icemet.cfg import Config

import argparse
import asyncio
import os

_default_config_file = os.path.join(home_path, "icemet-sensor.yaml")

def _parse_args():
	parser = argparse.ArgumentParser("ICEMET-sensor temperature relay parameter utility")
	parser.add_argument("cfg", nargs="?", default=_default_config_file, help="config file", metavar="str")
	parser.add_argument("-e", "--enable", action="store_true", help="enable relay")
	parser.add_argument("-d", "--disable", action="store_true", help="disable relay")
	return parser.parse_args()

def main():
	args = _parse_args()
	cfg = Config(args.cfg)
	
	plugins_paths = cfg.get("PLUGINS_PATHS", []) + [plugins_path]
	plugins = PluginContainer(cfg["PLUGINS_PATHS"])
	for name in cfg["PLUGINS"]:
		plugins.load(name)
	
	temp_relay = create_temp_relay(cfg["TEMP_RELAY_TYPE"], **cfg["TEMP_RELAY_OPT"])
	async def run():
		ret = await temp_relay.temp()
		print("Temperature: {}°C".format(ret[0]))
		if args.enable:
			await temp_relay.enable()
			print("Relay enabled")
		if args.disable:
			await temp_relay.disable()
			print("Relay disabled")
	asyncio.get_event_loop().run_until_complete(run())
