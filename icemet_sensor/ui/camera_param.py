from icemet_sensor import home_path, plugins_path
from icemet_sensor.camera import create_camera
from icemet_sensor.plugins import PluginContainer

from icemet.cfg import Config

import argparse
import os

_default_config_file = os.path.join(home_path, "icemet-sensor.yaml")

def _parse_args():
	parser = argparse.ArgumentParser("ICEMET-sensor camera parameter utility")
	parser.add_argument("cfg", nargs="?", default=_default_config_file, help="config file", metavar="str")
	parser.add_argument("-i", "--input", type=str, help="input file", metavar="str")
	parser.add_argument("-o", "--output", type=str, help="output file", metavar="str")
	return parser.parse_args()

def main():
	args = _parse_args()
	cfg = Config(args.cfg)
	
	plugins_paths = cfg.get("PLUGINS_PATHS", []) + [plugins_path]
	plugins = PluginContainer(cfg["PLUGINS_PATHS"])
	for name in cfg["PLUGINS"]:
		plugins.load(name)
	
	if "params" in cfg["CAMERA_OPT"]:
		cfg["CAMERA_OPT"]["params"] = None
	cam = create_camera(cfg["CAMERA_TYPE"], **cfg["CAMERA_OPT"])
	
	if args.output:
		cam.save_params(args.output)
		print("Parameters saved to '{}'".format(args.output))
	if args.input:
		cam.load_params(args.input)
		print("Parameters loaded from '{}'".format(args.input))
	if not args.input and not args.output:
		print("Nothing to do")
	cam.close()
