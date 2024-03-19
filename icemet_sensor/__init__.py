from collections import namedtuple
import os

version = "3.0.0-dev"
homedir = os.path.join(os.path.expanduser("~"), ".icemet")
datadir =  os.path.join(os.path.dirname(__file__), "data")

Context = namedtuple("Context", ["args", "cfg", "loop", "pool", "plugins", "quit"])
