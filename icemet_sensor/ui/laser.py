from icemet_sensor import home_path, plugins_path
from icemet_sensor.laser import create_laser
from icemet_sensor.plugins import PluginContainer

from icemet.cfg import Config

import argparse
import asyncio
import os

_default_config_file = os.path.join(home_path, "icemet-sensor.yaml")

def _create():
	parser = argparse.ArgumentParser("ICEMET-sensor laser utility")
	parser.add_argument("cfg", nargs="?", default=_default_config_file, help="config file", metavar="str")
	args = parser.parse_args()
	cfg = Config(args.cfg)
	
	plugins_paths = cfg.get("PLUGINS_PATHS", []) + [plugins_path]
	plugins = PluginContainer(plugins_paths)
	for name in cfg["PLUGINS"]:
		plugins.load(name)
	
	return create_laser(cfg["LASER_TYPE"], **cfg["LASER_OPT"])

def laser_on_main():
	laser = _create()
	asyncio.get_event_loop().run_until_complete(laser.on())
	print("Laser ON")

def laser_off_main():
	laser = _create()
	asyncio.get_event_loop().run_until_complete(laser.off())
	print("Laser OFF")
