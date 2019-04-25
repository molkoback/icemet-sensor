#!/usr/bin/python3

from icemet.camera import Camera

import argparse
import json

def _parse_args():
	parser = argparse.ArgumentParser("ICEMET camera parameter utility")
	parser.add_argument("-c", "--camera", type=int, default=0, help="camera id", metavar="int")
	parser.add_argument("-i", "--input", type=str, help="input file (.json)", metavar="str")
	parser.add_argument("-o", "--output", type=str, help="output file (.json)", metavar="str")
	return parser.parse_args()

if __name__ == "__main__":
	args = _parse_args()
	
	cam = Camera(args.camera)
	params = cam.params()
	for name, val in params.items():
		print("%s: %s" % (name, val))
	print()
	
	if args.output:
		with open(args.output, "w") as fp:
			json.dump(params, fp, sort_keys=True, indent=4)
		print("Parameters saved to '%s'" % args.output)
	if args.input:
		with open(args.input) as fp:
			cam.set_params(json.load(fp))
		print("Parameters loaded from '%s'" % args.input)
