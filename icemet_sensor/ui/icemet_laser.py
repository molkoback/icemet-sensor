from icemet_sensor import homedir
from icemet_sensor.laser import create_laser
from icemet_sensor.config import SensorConfig

import argparse
import asyncio
import os

_default_config_file = os.path.join(homedir, "icemet-sensor.yaml")

def _create():
	parser = argparse.ArgumentParser("ICEMET-sensor laser utility")
	parser.add_argument("cfg", nargs="?", default=_default_config_file, help="config file", metavar="str")
	args = parser.parse_args()
	cfg = SensorConfig(args.cfg)
	return create_laser(cfg.laser.name, **cfg.laser.kwargs)

def laser_on_main():
	laser = _create()
	asyncio.get_event_loop().run_until_complete(laser.on())
	print("Laser ON")

def laser_off_main():
	laser = _create()
	asyncio.get_event_loop().run_until_complete(laser.off())
	print("Laser OFF")
