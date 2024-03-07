from icemet_sensor import version, datadir, homedir
from icemet_sensor.measure import Measure
from icemet_sensor.plugins import PluginContainer
from icemet_sensor.status import Status
from icemet_sensor.uploader import Uploader
from icemet_sensor.util import collect_garbage

import aioftp
from icemet.cfg import Config

import argparse
import asyncio
from collections import namedtuple
import concurrent
from datetime import datetime
import logging
import os
import shutil
import sys

_version_str = """ICEMET-sensor {version}

Copyright (C) 2019-2020 Eero Molkoselkä <eero.molkoselka@gmail.com>
""".format(version=version)

_default_config_file = os.path.join(homedir, "icemet-sensor.yaml")

Context = namedtuple("Context", ["args", "cfg", "loop", "pool", "plugins", "quit"])

def _parse_args():
	parser = argparse.ArgumentParser("ICEMET-sensor")
	parser.add_argument("-c", "--config", type=str, help="config file (default: {})".format(_default_config_file), metavar="str", default=_default_config_file)
	parser.add_argument("-i", "--image", action="store_true", help="show image")
	parser.add_argument("-s", "--start", type=str, help="start time 'yyyy-mm-dd HH:MM:SS'", metavar="str")
	parser.add_argument("--start_now", action="store_true", help="start at the next minute")
	parser.add_argument("--start_next_10min", action="store_true", help="start at the next 10th minute")
	parser.add_argument("--start_next_hour", action="store_true", help="start at the next hour")
	parser.add_argument("--no_images", action="store_true", help="don't take images")
	parser.add_argument("--no_upload", action="store_true", help="don't upload images")
	parser.add_argument("--no_status", action="store_true", help="don't send status messages")
	parser.add_argument("-d", "--debug", action="store_true", help="enable debug messages")
	parser.add_argument("-V", "--version", action="store_true", help="print version information")
	return parser.parse_args()

def _init_logging(level):
	root = logging.getLogger()
	root.setLevel(level)
	ch = logging.StreamHandler(sys.stdout)
	ch.setLevel(level)
	if level == logging.DEBUG:
		fmt = "[%(asctime)s]<%(module)s:%(lineno)d>(%(levelname)s) %(message)s"
		aioftp.client.logger.setLevel(logging.DEBUG)
	else:
		fmt = "[%(asctime)s](%(levelname)s) %(message)s"
		aioftp.client.logger.setLevel(logging.ERROR)
	formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
	ch.setFormatter(formatter)
	root.addHandler(ch)

def _load_plugins(cfg):
	plugins = PluginContainer(cfg["PLUGINS_PATH"])
	for name in cfg["PLUGINS"]:
		plugins.load(name)
	return plugins

def _create_tasks(ctx):
	tasks = []
	if not ctx.args.no_images:
		tasks.append(ctx.loop.create_task(Measure(ctx).run()))
	if not ctx.args.no_upload:
		tasks.append(ctx.loop.create_task(Uploader(ctx).run()))
	if not ctx.args.no_status:
		tasks.append(ctx.loop.create_task(Status(ctx).run()))
	return tasks

def main():
	args = _parse_args()
	if args.version:
		sys.stdout.write(_version_str)
		sys.exit(0)
	
	# Logging
	_init_logging(logging.DEBUG if args.debug else logging.INFO)
	
	# Load config
	if args.config == _default_config_file and not os.path.exists(args.config):
		os.makedirs(os.path.split(args.config)[0], exist_ok=True)
		shutil.copy(os.path.join(datadir, "icemet-sensor.yaml"), args.config)
		logging.info("Config file created '{}'".format(args.config))
	
	# Async objects
	loop = asyncio.get_event_loop()
	pool = concurrent.futures.ThreadPoolExecutor()
	quit = asyncio.Event()
	
	# Create all instances
	tasks = []
	for file in args.config.split(","):
		cfg = Config(file)
		plugins = _load_plugins(cfg)
		ctx = Context(args, cfg, loop, pool, plugins, quit)
		plugins.call("on_init", ctx)
		logging.info("{} ({:02X})".format(cfg["SENSOR_TYPE"], cfg["SENSOR_ID"]))
		tasks += _create_tasks(ctx)
	
	# Garbage collection needed for some cameras
	if not args.no_images:
		tasks.append(loop.create_task(collect_garbage(quit, 2.0)))
	
	# Run
	if not tasks:
		sys.exit(1)
	async def _wait():
		for task in tasks:
			await task
	try:
		loop.run_until_complete(_wait())
		sys.exit(1)
	except KeyboardInterrupt:
		quit.set()
		loop.run_until_complete(_wait())
