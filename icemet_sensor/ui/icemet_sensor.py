from icemet_sensor import __version__
from icemet_sensor.sender import Sender
from icemet_sensor.sensor import Sensor
from icemet_sensor.saver import Saver
from icemet_sensor.config import SensorConfig
from icemet_sensor.data import Stack, Atomic

import argparse
from datetime import datetime
import logging
import os
import sys
import time

_version_str = """ICEMET Sensor {version}

Copyright (C) 2019 Eero Molkoselkä <eero.molkoselka@gmail.com>
""".format(version=__version__)
_default_cfg_file = os.path.join(os.path.expanduser("~"), ".icemet-sensor.yaml")

def _parse_args():
	parser = argparse.ArgumentParser("ICEMET Sensor")
	parser.add_argument("cfg", nargs="?", default=_default_cfg_file, help="config file", metavar="str")
	parser.add_argument("-s", "--start", type=str, help="start time 'yyyy-mm-dd HH:MM:SS'", metavar="str")
	parser.add_argument("--start_next_min", action="store_true", help="start at the next minute")
	parser.add_argument("--start_next_hour", action="store_true", help="start at the next hour")
	parser.add_argument("-F", "--offline", action="store_true", help="don't send images over FTP")
	#parser.add_argument("-Q", "--quit", action="store_true", help="quit after one measurement (offline)")
	parser.add_argument("-d", "--debug", action="store_true", help="enable debug messages")
	parser.add_argument("-V", "--version", action="store_true", help="print version information")
	return parser.parse_args()

def _init_logging(level):
	root = logging.getLogger()
	root.setLevel(level)
	ch = logging.StreamHandler(sys.stdout)
	ch.setLevel(level)
	formatter = logging.Formatter(
		"[%(asctime)s]<%(name)s>(%(levelname)s) %(message)s",
		datefmt="%H:%M:%S"
	)
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
		kwargs["quit"] = Atomic(False)
		kwargs["stack"] = Stack(1)
		kwargs["cfg"] = SensorConfig(args.cfg)
		
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
			Saver.start(**kwargs)
		]
		if not args.offline:
			threads.append(Sender.start(**kwargs))
		
		# Wait for threads
		while not kwargs["quit"].get():
			for thread in threads:
				if not thread.is_alive():
					kwargs["quit"].set(True)
					sys.exit(1)
			time.sleep(0.1)
	
	except Exception as err:
		log.critical(str(err))
		sys.exit(1)
	
	except KeyboardInterrupt:
		kwargs["quit"].set(True)
		log.info("Exiting")
