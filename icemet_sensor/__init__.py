from collections import namedtuple
import os

version = "3.0.0-dev"
home_path = os.path.join(os.path.expanduser("~"), ".icemet")
data_path =  os.path.join(os.path.dirname(__file__), "data")
plugins_path = os.path.join(os.path.dirname(__file__), "plugins")

Context = namedtuple("Context", ["args", "cfg", "loop", "pool", "plugins", "quit"])
