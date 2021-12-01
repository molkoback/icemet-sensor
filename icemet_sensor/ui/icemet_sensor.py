from icemet_sensor import Context, version, homedir
from icemet_sensor.config import create_config_file, SensorConfig
from icemet_sensor.measure import Measure
from icemet_sensor.status import Status
from icemet_sensor.uploader import Uploader
from icemet_sensor.util import collect_garbage

import aioftp

import argparse
import asyncio
from datetime import datetime
import logging
import os
import sys
import time

_version_str = """ICEMET-sensor {version}

Copyright (C) 2019-2020 Eero Molkoselkä <eero.molkoselka@gmail.com>
""".format(version=version)

_default_config_file = os.path.join(homedir, "icemet-sensor.yaml")

def _parse_args():
	parser = argparse.ArgumentParser("ICEMET-sensor")
	parser.add_argument("-c", "--config", type=str, help="config file (default: {})".format(_default_config_file), metavar="str", default=_default_config_file)
	parser.add_argument("-i", "--image", action="store_true", help="show image")
	parser.add_argument("-s", "--start", type=str, help="start time 'yyyy-mm-dd HH:MM:SS'", metavar="str")
	parser.add_argument("--start_now", action="store_true", help="start at the next minute")
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

def main():
	ctx = Context()
	ctx.args = _parse_args()
	if ctx.args.version:
		sys.stdout.write(_version_str)
		sys.exit(0)
	
	_init_logging(logging.DEBUG if ctx.args.debug else logging.INFO)
	
	if ctx.args.config == _default_config_file and not os.path.exists(ctx.args.config):
		create_config_file(ctx.args.config)
		logging.info("Config file created '{}'".format(ctx.args.config))
	ctx.cfg = SensorConfig(ctx.args.config)
	
	logging.info("{} ({:02X})".format(ctx.cfg.sensor.type, ctx.cfg.sensor.id))
	
	# Create tasks
	tasks = []
	if not ctx.args.no_images:
		tasks.append(ctx.loop.create_task(collect_garbage(ctx, 2.0)))
		tasks.append(ctx.loop.create_task(Measure(ctx).run()))
	if not ctx.args.no_upload:
		tasks.append(ctx.loop.create_task(Uploader(ctx).run()))
	if not ctx.args.no_status:
		tasks.append(ctx.loop.create_task(Status(ctx).run()))
	if not tasks:
		sys.exit(1)
	
	# Run
	async def _wait():
		for task in tasks:
			await task
	try:
		ctx.loop.run_until_complete(_wait())
		sys.exit(1)
	except KeyboardInterrupt:
		ctx.quit.set()
		ctx.loop.run_until_complete(_wait())
