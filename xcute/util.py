#! python3

import datetime
import sys

# config object. Task runner will use this dict to expand format string.
conf = {
	"date": datetime.datetime.now(),
	"tty": bool(sys.stdout and sys.stdout.isatty())
}

def expand_conf(text):
	"""Expand format string with config"""
	return text.format_map(conf)

def log(*text):
	"""Log text"""
	if conf["tty"]:
		print(*text)

class Wrapper:
	"""A wrapper class that init targets"""
	def __init__(self, *targets):
		self.targets = targets
