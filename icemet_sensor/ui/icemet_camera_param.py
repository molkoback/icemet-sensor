from icemet_sensor.camera import createCamera
from icemet_sensor.config import default_file, SensorConfig

import argparse
import json

def _parse_args():
	parser = argparse.ArgumentParser("ICEMET camera parameter utility")
	parser.add_argument("cfg", nargs="?", default=default_file, help="config file", metavar="str")
	parser.add_argument("-c", "--camera", type=int, default=0, help="camera id", metavar="int")
	parser.add_argument("-i", "--input", type=str, help="input file (.json)", metavar="str")
	parser.add_argument("-o", "--output", type=str, help="output file (.json)", metavar="str")
	return parser.parse_args()

def main():
	args = _parse_args()
	cfg = SensorConfig(args.cfg)
	
	cam = createCamera(cfg.camera.type, **cfg.camera.kwargs)
	params = cam.params()
	for name, val in params.items():
		print("{}: {}".format(name, val))
	print()
	
	if args.output:
		with open(args.output, "w") as fp:
			json.dump(params, fp, sort_keys=True, indent=4)
		print("Parameters saved to '{}'".format(args.output))
	if args.input:
		with open(args.input) as fp:
			cam.set_params(json.load(fp))
		print("Parameters loaded from '{}'".format(args.input))
