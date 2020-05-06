from icemet_sensor import version
from icemet_sensor.manager import Manager
from icemet_sensor.sender import Sender
from icemet_sensor.sensor import Sensor
from icemet_sensor.config import default_file, create_default_file, SensorConfig
from icemet_sensor.data import Stack, Atomic

import argparse
from datetime import datetime
import logging
import os
import sys
import time

_version_str = """ICEMET-sensor {version}

Copyright (C) 2019-2020 Eero Molkoselkä <eero.molkoselka@gmail.com>
""".format(version=version)

def _parse_args():
	parser = argparse.ArgumentParser("ICEMET-sensor")
	parser.add_argument("-c", "--config", type=str, help="config file (default: {})".format(default_file), metavar="str", default=default_file)
	parser.add_argument("-s", "--start", type=str, help="start time 'yyyy-mm-dd HH:MM:SS'", metavar="str")
	parser.add_argument("--start_next_min", action="store_true", help="start at the next minute")
	parser.add_argument("--start_next_hour", action="store_true", help="start at the next hour")
	parser.add_argument("-F", "--offline", action="store_true", help="don't send images over FTP")
	#parser.add_argument("-Q", "--quit", action="store_true", help="quit after one measurement (offline)")
	parser.add_argument("-d", "--debug", action="store_true", help="enable debug messages")
	parser.add_argument("-V", "--version", action="store_true", help="print version information")
	return parser.parse_args()

def _init_logging(level):
	if level == logging.DEBUG:
		fmt = "[%(asctime)s]<%(name)s>(%(levelname)s) %(message)s"
	else:
		fmt = "[%(asctime)s] %(message)s"
	root = logging.getLogger()
	root.setLevel(level)
	ch = logging.StreamHandler(sys.stdout)
	ch.setLevel(level)
	formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
	ch.setFormatter(formatter)
	root.addHandler(ch)

def main():
	args = _parse_args()
	if args.version:
		sys.stdout.write(_version_str)
		sys.exit(0)
	
	_init_logging(logging.DEBUG if args.debug else logging.INFO)
	log = logging.getLogger("MAIN")
	
	kwargs = {}
	try:
		if args.config == default_file and not os.path.exists(args.config):
			create_default_file()
			logging.info("Config file created '{}'".format(args.config))
		
		kwargs["quit"] = Atomic(False)
		kwargs["stack"] = Stack(1)
		kwargs["cfg"] = SensorConfig(args.config)
		
		# Set the start time
		if args.start:
			kwargs["start_time"] = datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S")
		elif args.start_next_min:
			kwargs["start_time"] = datetime.fromtimestamp(int(time.time()) // 60 * 60 + 60)
		elif args.start_next_hour:
			kwargs["start_time"] = datetime.fromtimestamp(int(time.time()) // 3600 * 3600 + 3600)
		else:
			kwargs["start_time"] = datetime.fromtimestamp(int(time.time()) + 5)
		
		# Start worker threads
		threads = [
			Sensor.start(**kwargs),
			Manager.start(**kwargs)
		]
		if not args.offline and kwargs["cfg"].ftp.enable:
			threads.append(Sender.start(**kwargs))
		
		# Wait for threads
		while not kwargs["quit"].get():
			for thread in threads:
				if not thread.is_alive():
					kwargs["quit"].set(True)
					sys.exit(1)
			time.sleep(0.1)
	
	except Exception as e:
		log.critical(log.critical("{}: {}".format(e.__class__.__name__, e)))
		sys.exit(1)
	
	except KeyboardInterrupt:
		kwargs["quit"].set(True)
		log.info("Exiting")
