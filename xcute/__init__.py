#! python3

from __future__ import print_function

from .__pkginfo__ import __version__

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

# config object. Task runner will use this dict to expand format string.
conf = {
    "date": datetime.datetime.now(),
    "tty": bool(sys.stdout and sys.stdout.isatty())
}
"""A dictionary that is used across all tasks. It has 2 purpoeses: 

1. A convenience way to share variables between your ``cute.py`` file and 
  ``xcute`` module.
2. The context for string formatting. See :func:`f`.

By default, it has following keys:

* ``pkg_name``: The ``pkg_name`` specified by the user in :func:`cute`.
* ``date``: Equals to ``datetime.datetime.now()``.
* ``tty``: ``bool``. ``True`` if the output is a terminal.
* ``version``: ``str``. A version number. Also see :func:`cute`.
* ``old_version``: ``str``. A version number. Only available after
  :class:`Bump` task.
* ``tasks``: ``dict``. This is what you send to :func:`cute`.
* ``curr_task``: ``str``. The name of the current task.
"""


def f(text):
    """Format the string with :const:`conf`.
    
    :arg str text: Input string.
    :rtype: str
    
    This function is used by various task executors. It allows you to interpret
    variables in your tasks. For example::
    
      cute(
        hello = "echo Current time is {date}"
      )
    """
    return text.format_map(conf)

def version_from_file(file):
    """Extract the version number from a file.
    
    :arg path-like file: Input file.
    :rtype: str
    """
    text = pathlib.Path(file).read_text(encoding="utf-8")
    return split_version(text)[1]
        
def split_version(text):
    """Split the text to ``(left, version_number, right)``.
    
    :arg str text: Input text. It is usually the source code of ``__init__.py``
        or ``__pkginfo__.py``.
    :rtype: tuple(str, str, str)
    
    The regular expression used by this function::
    
        match = re.search("__version__ = ['\\"]([^'\\"]+)", text)
    """
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
    """Log the items to the console.
    
    If ``conf["tty"]`` is False, this function has no effect.
    
    :arg list items: The items would be logged with ``pring(*items)``.
    """
    if conf["tty"]:
        print(*items)
        
def exc(message=None):
    """Raise an exception. If ``message`` is None, it re-raise last exception.
    
    It is usually used in a ``xxx_err`` task to re-raise the exception::
    
        from xcute import cute, exc

        cute(
            task = "do something wrong",
            # re-raise the exception so the process exits with non-zero
            # exit code
            task_err = ["handle error", Exception]
        )
    """
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
            log("> Cmd: {}".format(" ".join(args)))
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
        import semver

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
    def __init__(self, err=None):
        self.err = err
        
    def __call__(self):
        if not self.err:
            raise # pylint: disable=misplaced-bare-raise
        if isclass(self.err):
            raise self.err()
        if isinstance(self.err, str):
            raise Exception(self.err)
        raise self.err
            
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

    Define your tasks as keyword arguments. Those tasks would be assigned to
    :const:`conf`::
    
        conf["tasks"] = tasks
        
    There are some tasks having special effects:

    * ``pkg_name``: When this task is defined:
    
      - The key is removed and inserted into :const:`conf`. This allows you to
        specify ``{pkg_name}`` variable in other tasks.
        
      - The module would try to find version number from
        ``{pkg_name}/__init__.py`` and ``{pkg_name}/__pkginfo__.py``. If found,
        The filename is inserted to :const:`conf` with key ``version_file``, and
        the version is inserted as ``version``.

        See :func:`split_version` for the regular expression matching
        ``__version__``.
        
    Some tasks have a default value:
      
    * ``version``: If not provided, it defaults to ``Log("{version}")``.
    * ``bump``: If not provided, it defaults to ``Bump("{version_file}")``.
    """
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
    log("> Task: {}".format(name))
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
