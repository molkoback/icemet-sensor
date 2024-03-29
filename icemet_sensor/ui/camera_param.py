from icemet_sensor import homedir
from icemet_sensor.camera import create_camera
from icemet_sensor.config import SensorConfig

import argparse
import os

_default_config_file = os.path.join(homedir, "icemet-sensor.yaml")

def _parse_args():
	parser = argparse.ArgumentParser("ICEMET-sensor camera parameter utility")
	parser.add_argument("cfg", nargs="?", default=_default_config_file, help="config file", metavar="str")
	parser.add_argument("-i", "--input", type=str, help="input file", metavar="str")
	parser.add_argument("-o", "--output", type=str, help="output file", metavar="str")
	return parser.parse_args()

def main():
	args = _parse_args()
	cfg = SensorConfig(args.cfg)
	cfg.camera.kwargs["params"] = None
	cam = create_camera(cfg.camera.name, **cfg.camera.kwargs)
	if args.output:
		cam.save_params(args.output)
		print("Parameters saved to '{}'".format(args.output))
	if args.input:
		cam.load_params(args.input)
		print("Parameters loaded from '{}'".format(args.input))
	if not args.input and not args.output:
		print("Nothing to do")
	cam.close()
