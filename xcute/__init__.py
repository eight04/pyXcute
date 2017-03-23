#! python3

import sys
import shlex
import subprocess
import pathlib
import traceback

import semver

from .util import Wrapper, conf, expand_conf, log
from .version import Version # pylint: disable=unused-import
from .version import split_version, find_version_file

__version__ = "0.3.0"

class Cmd(Wrapper):
	"""Command line runner"""	
	def __call__(self, *args):
		"""Arguments will be appended to each command. [Expand format string]
		"""
		for target in self.targets:
			target = expand_conf(target)
			args = shlex.split(target) + list(args)
			subprocess.run(args, shell=True, check=True)
		
class Bump(Wrapper):
	"""Bump version runner"""
	def __call__(self, part="patch"):
		"""Bump version number. [Expand format string]

		It use split_version to find the version in a file. After bumping, it
		will export "old_version", "version", and "file" into config.
		
		See semver.bump_X for valid arguments.
		"""
		for file in self.targets:
			file = pathlib.Path(expand_conf(file))
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
			
class Task(Wrapper):
	"""User task runner"""
	def __call__(self, *args):
		"""It treat each target as task name and execute it"""
		for target in self.targets:
			run_main(target, args)
		
class Log(Wrapper):
	"""A printer"""
	def __call__(self):
		"""It print things. [Expand format string]"""
		print(*map(expand_conf, self.targets))
		
class Chain(Wrapper):
	"""Chain task runner"""
	def __call__(self, *args):
		"""It chain tasks.

		Note that the argument will be passed into EACH task.
		"""
		for target in self.targets:
			for item in target:
				run_task(item, *args)
			
class Exc(Wrapper):
	"""Throw error"""
	def __call__(self, *args):
		"""It just throw error"""
		if self.targets:
			raise Exception(*self.targets)
		else:
			raise # pylint: disable=misplaced-bare-raise
	
class Exit(Wrapper):
	"""Exit"""
	def __call__(self, *args):
		"""It just exit"""
		sys.exit(*self.targets)
	
def cute(**tasks):
	"""Main entry point.

	Define your tasks as keyword arguments just like setuptools.setup().
	Export "tasks", which is a dict, to config."""
	conf["tasks"] = tasks
	
	if "pkg_name" in tasks:
		conf["pkg_name"] = tasks["pkg_name"]
		del tasks["pkg_name"]
		
		filename = find_version_file()
		if filename and "bump" not in tasks:
			tasks["bump"] = Bump("{{pkg_name}}/{}.py".format(filename))
			
		if "version" not in tasks:
			tasks["version"] = Log("{version}")
	
	parse_arg(sys.argv[1:])
	try:
		run_main(conf["init"], conf["args"])
	except subprocess.CalledProcessError as err:
		# printing stack trace of process error doesn't help
		print(err)
		sys.exit(1)
	except Exception: # pylint: disable=broad-except
		traceback.print_exc()
		sys.exit(1)

def parse_arg(arg):
	"""Parse sys.argv. Export "init", "args" to config."""
	if len(arg) < 1:
		conf["init"] = "default"
	else:
		conf["init"] = arg[0]
	conf["args"] = arg[1:]

def run_main(name, args):
	"""Run task with specific name.

	This function handles _pre, _err, _post suffix.
	"""
	if name not in conf["tasks"]:
		raise Exception("Cannot find {name!r} in the cute file".format(name=name))
		
	run(name + "_pre")
	try:
		run(name, args)
	except Exception: # pylint: disable=broad-except
		if not run(name + "_err"):
			raise
	else:
		run(name + "_post")
	finally:
		run(name + "_fin")

def run(name, args=None):
	"""Run middleware. It converts task name into user task if possible."""
	if name not in conf["tasks"]:
		return False
		
	conf["name"] = name
	log("{name}...".format(name=name))
		
	run_task(conf["tasks"][name], args)
	return True
	
def run_task(task, args=None):
	"""Run user task.

	It handles non-callable user task and converts them into Chain, Task or
	Cmd.
	"""
	if not callable(task):
		if isinstance(task, list):
			task = Chain(task)
		elif task in conf["tasks"]:
			task = Task(task)
		else:
			task = Cmd(task)
		
	if not callable(task):
		raise Exception("{task!r} is not callable".format(task=task))

	conf["task"] = task
	
	if args is not None:
		task(*args)
	else:
		task()
