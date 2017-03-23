#! python3

import re
import pathlib

from .util import Wrapper, conf, expand_conf

class Version(Wrapper):
	"""Grab version"""
	def __call__(self):
		"""It will find version from target and export it to config.
		[Expand format string]
		"""
		conf["version"] = version_from_file(expand_conf(self.targets[-1]))
		
def version_from_file(file):
	"""A helper to extract version from file"""
	text = pathlib.Path(file).read_text(encoding="utf-8")
	return split_version(text)[1]
		
def split_version(text):
	"""Split text to (left, version_number, right)."""
	match = re.search("__version__ = ['\"]([^'\"]+)", text)
	i = match.start(1)
	j = match.end(1)
	return text[:i], text[i:j], text[j:]

def find_version_file():
	"""Find version from following locations
	
	{pkg_name}/__init__.py
	{pkg_name}/__pkginfo__.py
	
	and return filename without extension and folder.
	"""
	for file in ("__init__", "__pkginfo__"):
		try:
			Version("{{pkg_name}}/{}.py".format(file))()
			return file
		except (OSError, AttributeError):
			pass
