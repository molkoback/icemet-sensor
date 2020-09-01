from icemet_sensor import version, homedir
from icemet_sensor.config import create_config_file, SensorConfig
from icemet_sensor.measure import Measure
from icemet_sensor.sender import Sender
from icemet_sensor.sensor import Sensor
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
_ret = 0

def _parse_args():
	parser = argparse.ArgumentParser("ICEMET-sensor")
	parser.add_argument("-c", "--config", type=str, help="config file (default: {})".format(_default_config_file), metavar="str", default=_default_config_file)
	parser.add_argument("-s", "--start", type=str, help="start time 'yyyy-mm-dd HH:MM:SS'", metavar="str")
	parser.add_argument("--start_next_min", action="store_true", help="start at the next minute")
	parser.add_argument("--start_next_hour", action="store_true", help="start at the next hour")
	parser.add_argument("-F", "--offline", action="store_true", help="don't send images over FTP")
	parser.add_argument("-S", "--send_only", action="store_true", help="only send existing images")
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

def _error(e):
	global _ret
	logging.critical("{}: {}".format(e.__class__.__name__, e))
	_ret = 1

def _handler(loop, ctx):
	e = ctx["exception"]
	if not isinstance(e, KeyboardInterrupt):
		_error(e)
	loop.stop()

def main():
	args = _parse_args()
	if args.version:
		sys.stdout.write(_version_str)
		sys.exit(0)
	
	_init_logging(logging.DEBUG if args.debug else logging.INFO)
	
	try:
		if args.config == _default_config_file and not os.path.exists(args.config):
			create_config_file(args.config)
			logging.info("Config file created '{}'".format(args.config))
		cfg = SensorConfig(args.config)
		
		# Set the start time
		now = int(time.time())
		if args.start:
			start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp()
		elif args.start_next_min:
			start_time = now // 60 * 60 + 60
		elif args.start_next_hour:
			start_time = now // 3600 * 3600 + 3600
		else:
			start_time = now // 10 * 10 + 10
		
		# Start tasks
		logging.info("ICEMET-sensor {:02X}".format(cfg.sensor.id))
		tasks = []
		if not args.send_only:
			tasks.append(collect_garbage(5))
			tasks.append(Measure(cfg, start_time, Sensor(cfg)).run())
		if not args.offline and cfg.ftp.enable:
			tasks.append(Sender(cfg).run())
		if not tasks:
			sys.exit(1)
		loop = asyncio.get_event_loop()
		loop.set_exception_handler(_handler)
		for task in tasks:
			loop.create_task(task)
		loop.run_forever()
	
	except Exception as e:
		_error(e)
	except KeyboardInterrupt:
		logging.info("Exiting")
	sys.exit(_ret)
