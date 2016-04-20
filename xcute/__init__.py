import sys
import datetime
import shlex
import subprocess
import pathlib
import semver
import re
import traceback
import itertools

__version__ = "0.1.2"

class Wrapper:
	"""A wrapper class that init targets"""
	def __init__(self, *targets):
		self.targets = targets

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
			if bump:
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
		
class Version(Wrapper):
	"""Grab version"""
	def __call__(self):
		"""It will find version from target and export it to config.
		[Expand format string]
		
		See split_version.
		"""
		target = pathlib.Path(expand_conf(self.targets[-1]))
		text = target.read_text(encoding="utf-8")
		conf["version"] = split_version(text)[1]
		
class Log(Wrapper):
	"""A printer"""
	def __call__(self):
		"""It print things. [Expand format string]"""
		print(*map(expand_conf, self.targets))
		
class Chain(Wrapper):
	"""Chain task runner"""
	def __init__(self, *targets):
		self.targets = list(itertools.chain(*targets))
	def __call__(self, *args):
		"""It chain tasks.

		Note that the argument will be passed into EACH task.
		"""
		for target in self.targets:
			run_task(target, *args)
	
# config object. Task runner will use this dict to expand format string.
conf = {
	"date": datetime.datetime.now(),
	"tty": sys.stdout and sys.stdout.isatty()
}

def expand_conf(text):
	"""Expand format string with config"""
	return text.format_map(conf)

def split_version(text):
	"""Split text to (left, version_number, right)."""
	match = re.search("__version__ = ['\"]([^'\"]+)", text)
	i = match.start(1)
	j = match.end(1)
	return text[:i], text[i:j], text[j:]

def log(*text):
	"""Log text"""
	if conf["tty"]:
		print(*text)
			
def cute(**tasks):
	"""Main entry point.

	Define your tasks as keyword arguments just like setuptools.setup().
	Export "tasks", which is a dict, to config."""
	conf["tasks"] = tasks
	parse_arg(sys.argv[1:])
	try:
		run_main(conf["init"], conf["args"])
	except subprocess.CalledProcessError as err:
		# printing stack trace of process error doesn't help
		print(err)
		sys.exit(1)
	except:
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
	except Exception:
		if name + "_err" not in conf["tasks"]:
			raise
		run(name + "_err")
	else:
		run(name + "_post")

def run(name, args=[]):
	"""Run middleware. It converts task name into user task if possible."""
	if name not in conf["tasks"]:
		return
		
	conf["name"] = name
	log("{name}...".format(name=name))
		
	run_task(conf["tasks"][name], args)
	
def run_task(task, args=[]):
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
	
	task(*args)
