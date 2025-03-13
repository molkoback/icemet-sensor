from icemet_sensor import version, data_path, home_path, plugins_path, Context
from icemet_sensor.measure import Measure
from icemet_sensor.plugins import PluginContainer
from icemet_sensor.util import logger

from icemet.cfg import Config

import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import shutil
import sys

_version_str = """ICEMET-sensor {version}

Copyright (C) 2019-2025 Eero Molkoselkä <eero.molkoselka@gmail.com>
""".format(version=version)

_default_config_file = os.path.join(home_path, "icemet-sensor.yaml")

def _parse_args():
	parser = argparse.ArgumentParser("ICEMET-sensor")
	parser.add_argument("-c", "--config", type=str, help="comma separated list of config files (default: {})".format(_default_config_file), metavar="str", default=_default_config_file)
	parser.add_argument("-s", "--start", type=str, help="start time 'yyyy-mm-dd HH:MM:SS'", metavar="str")
	parser.add_argument("--start_now", action="store_true", help="start at the next minute")
	parser.add_argument("--start_next_10min", action="store_true", help="start at the next 10th minute")
	parser.add_argument("--start_next_hour", action="store_true", help="start at the next hour")
	parser.add_argument("--no_images", action="store_true", help="don't take images")
	parser.add_argument("-d", "--debug", action="store_true", help="enable debug messages")
	parser.add_argument("-V", "--version", action="store_true", help="print version information")
	return parser.parse_args()

def _init_logger(level):
	if level == logging.DEBUG:
		root = logging.getLogger()
		fmt = "[%(asctime)s]<%(module)s:%(lineno)d>(%(levelname)s) %(message)s"
	else:
		root = logger
		fmt = "[%(asctime)s](%(levelname)s) %(message)s"
	
	root.setLevel(level)
	ch = logging.StreamHandler(sys.stdout)
	ch.setLevel(level)
	formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
	ch.setFormatter(formatter)
	root.addHandler(ch)

async def _collect():
	tasks = asyncio.all_tasks()
	for task in tasks:
		if task.get_coro().__name__ != "_collect":
			await task

def main():
	args = _parse_args()
	if args.version:
		sys.stdout.write(_version_str)
		return 0
	
	# Logging
	_init_logger(logging.DEBUG if args.debug else logging.INFO)
	
	# Load config
	if args.config == _default_config_file and not os.path.exists(args.config):
		os.makedirs(os.path.split(args.config)[0], exist_ok=True)
		shutil.copy(os.path.join(data_path, "icemet-sensor.yaml"), args.config)
		logger.info("Config file created '{}'".format(args.config))
	
	# Async objects
	loop = asyncio.get_event_loop()
	pool = ThreadPoolExecutor()
	quit = asyncio.Event()
	
	# Create all instances
	for file in args.config.split(","):
		cfg = Config(file)
		
		# Load plugins
		plugins_paths = cfg.get("PLUGINS_PATHS", []) + [plugins_path]
		logger.debug("Plugins paths: {}".format(", ".join(plugins_paths)))
		plugins = PluginContainer(plugins_paths)
		for name in cfg["PLUGINS"]:
			hooks = plugins.load(name)
			logger.debug("Plugin '{}' with {} hooks".format(name, hooks))
		
		# Create context
		ctx = Context(args, cfg, loop, pool, plugins, quit)
		logger.info("{} ({:02X})".format(cfg["SENSOR_TYPE"], cfg["SENSOR_ID"]))
		loop.run_until_complete(plugins.call("on_init", ctx))
		
		if not args.no_images:
			ctx.loop.create_task(Measure(ctx).run())
	
	# Run
	try:
		loop.run_until_complete(_collect())
		return 1
	except KeyboardInterrupt:
		quit.set()
		loop.run_until_complete(_collect())
	return 0
