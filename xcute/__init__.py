#! python3

from __future__ import print_function

from contextlib import contextmanager
import datetime
from inspect import isclass
import re
try:
	import pathlib2 as pathlib
except ImportError:
	import pathlib
import sys
import shlex
import subprocess
import traceback

import semver

from .__pkginfo__ import __version__

# config object. Task runner will use this dict to expand format string.
conf = {
	"date": datetime.datetime.now(),
	"tty": bool(sys.stdout and sys.stdout.isatty())
}

def f(text): # pylint: disable=invalid-name
	"""format string."""
	return text.format_map(conf)

def version_from_file(file):
	"""Extract version from file"""
	text = pathlib.Path(file).read_text(encoding="utf-8")
	return split_version(text)[1]
		
def split_version(text):
	"""Split text to (left, version_number, right)."""
	match = re.search("__version__ = ['\"]([^'\"]+)", text)
	i = match.start(1)
	j = match.end(1)
	return text[:i], text[i:j], text[j:]

def find_version_file():
	"""Extract version, version_file to conf"""
	if "pkg_name" not in conf:
		return
		
	for file in ("__init__", "__pkginfo__"):
		filename = "{}/{}.py".format(conf["pkg_name"], file)
		try:
			conf["version"] = version_from_file(filename)
			conf["version_file"] = filename
		except (OSError, AttributeError):
			pass
			
def log(*items):
	if conf["tty"]:
		print(*items)
		
def exc(message=None):
	"""Raise exception. If message is None, reraise last exception."""
	if message is None:
		raise # pylint: disable=misplaced-bare-raise
	raise Exception(message)
	
def noop(*args, **kwargs):
	"""A noop"""
	pass

class Cmd:
	"""Command line runner"""
	def __init__(self, *cmds):
		self.cmds = cmds
		
	def __call__(self, *args):
		"""args are appended to each command."""
		for cmd in self.cmds:
			args = shlex.split(f(cmd)) + list(args)
			subprocess.run(args, shell=True, check=True)
		
class Bump:
	"""Bump version runner"""
	def __init__(self, file):
		self.file = file
		
	def __call__(self, part="patch"):
		"""Bump version number. [Expand format string]

		It use split_version to find the version in a file. After bumping, it
		will export "old_version", "version", and "file" into config.
		
		See semver.bump_X for valid arguments.
		"""
		file = pathlib.Path(f(self.file))
		conf["file"] = file
		left, old_version, right = split_version(file.read_text(encoding="utf-8"))
		bump = getattr(semver, "bump_" + part, None)
		conf["old_version"] = old_version
		if callable(bump):
			version = bump(old_version)
		else:
			version = part
			semver.parse(version)
		conf["version"] = version
		file.write_text(left + version + right, encoding="utf-8")
		log("Bump {file} from {old_version} to {version}".format(
			file=file,
			old_version=old_version,
			version=version
		))
			
class Task:
	"""Run conf["tasks"][name]"""
	def __init__(self, name):
		self.name = name
		
	def __call__(self, *args):
		run(self.name, *args)
		
class Log:
	"""A printer"""
	def __init__(self, *items):
		self.items = items
		
	def __call__(self):
		for item in self.items:
			if isinstance(item, str):
				item = f(item)
			log(item)
		
class Chain:
	"""Chain task runner"""
	def __init__(self, *task_lists):
		self.task_lists = task_lists
		
	def __call__(self, *args):
		"""It chain tasks.

		Note that the argument will be passed into EACH task.
		"""
		for list in self.task_lists:
			for item in list:
				run_task(item, *args)
				
class Throw:
	"""Throw error"""
	def __init__(self, exc=None, message=None):
		self.exc = exc
		self.message = message
		
	def __call__(self):
		if isclass(self.exc):
			err = self.exc(self.message)
		else:
			err = self.exc
		if err:
			raise err
		raise # pylint: disable=misplaced-bare-raise
			
class Try:
	"""Suppress error"""
	def __init__(self, *tasks):
		self.tasks = tasks
		
	def __call__(self, *args):
		for task in self.tasks:
			try:
				run_task(task, *args)
			except Exception as err: # pylint: disable=broad-except
				log(err)

def cute(**tasks):
	"""Main entry point.

	Define your tasks as keyword arguments just like setuptools.setup().
	Export "tasks", which is a dict, to config."""
	conf["tasks"] = tasks
	
	if "pkg_name" in tasks:
		conf["pkg_name"] = tasks["pkg_name"]
		del tasks["pkg_name"]
		
	find_version_file()
	
	if "bump" not in tasks:
		tasks["bump"] = Bump("{version_file}")
		
	if "version" not in tasks:
		tasks["version"] = Log("{version}")
	
	args = parse_args()
	task_name = args[0]
	args = args[1:]
	
	try:
		run(task_name, *args)
	except subprocess.CalledProcessError as err:
		# printing stack trace of process error doesn't help
		log(err)
		exit(1)
	except Exception: # pylint: disable=broad-except
		traceback.print_exc()
		exit(1)
	
def parse_args(args=None):
	"""Parse sys.argv. Export "init", "args" to config."""
	if args is None:
		args = sys.argv[1:]
		
	if args:
		return args
		
	return ("default",)

def run(name, *args):
	"""Run task with specific name.

	This function handles _pre, _err, _post suffix.
	"""
	if name not in conf["tasks"]:
		raise Exception("Cannot find {name!r} in the cute file".format(name=name))
		
	do_run(name + "_pre")
	try:
		do_run(name, *args)
	except Exception: # pylint: disable=broad-except
		if not do_run(name + "_err"):
			raise
	else:
		do_run(name + "_post")
	finally:
		do_run(name + "_fin")
		
def iterable(obj):
	try:
		iter(obj)
	except TypeError:
		return False
	return True
		
@contextmanager
def enter_task(name):
	curr_task = conf.get("curr_task")
	conf["curr_task"] = name
	log("{}...".format(name))
	yield
	conf["curr_task"] = curr_task

def do_run(name, *args):
	"""Run middleware. It converts task name into user task if possible."""
	task = conf["tasks"].get(name)
	if not task:
		return False
		
	with enter_task(name):
		run_task(task, *args)
		
	return True
	
class Transformer:
	def __init__(self):
		self.matchers = []
		
	def add(self, convert):
		def wrapped(match):
			self.matchers.append((match, convert))
			return match
		return wrapped
		
	def transform(self, item):
		for match, convert in self.matchers:
			if match(item):
				return convert(item)
		return item
	
def run_task(task, *args):
	"""Run user task.

	It handles non-callable user task and converts them into Chain, Task or
	Cmd.
	"""
	task = t.transform(task)
		
	if not callable(task):
		raise Exception("{task!r} is not callable".format(task=task))

	task(*args)
	
t = Transformer()

@t.add(Task)
def _(task):
	return isinstance(task, str) and task in conf.get("tasks", ())

@t.add(Cmd)
def _(task):
	return isinstance(task, str)
	
@t.add(Chain)
def _(task):
	try:
		iter(task)
	except TypeError:
		return False
	return True
	
@t.add(Throw)
def _(task):
	if isinstance(task, BaseException):
		return True
	if isclass(task) and issubclass(task, BaseException):
		return True
	return False
