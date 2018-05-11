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
    
    :arg list items: ``items`` would be logged with ``print(*items)``.
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
    
class Cmd:
    """Shell command executor."""
    def __init__(self, *cmds):
        """
        :arg list[str] cmds: A list of commands. The command may contain
            variables which could be expanded by :func:`f`.
            
        If the task is a ``str``, the task would be converted into
        :class:`Cmd`::
        
            cute(
                foo = "echo foo"
            )
            # equals to
            cute(
                foo = Cmd("echo foo")
            )
        """
        self.cmds = cmds
        
    def __call__(self, *args):
        """When called, it executes each commands with :func:`subprocess.run`.
        
        :arg list[str] args: ``args`` are appended to each command.
        """
        for cmd in self.cmds:
            args = shlex.split(f(cmd)) + list(args)
            log("> Cmd: {}".format(" ".join(args)))
            subprocess.run(args, shell=True, check=True)
        
class Bump:
    """An executor which can bump the version inside a .py file."""
    def __init__(self, file):
        """
        :arg str file: Input file.
        """
        self.file = file
        
    def __call__(self, part="patch"):
        """When called, it bumps the version number of the file.

        :arg str part: Specify which part should be bumped. Possible values are
            ``"patch"``, ``"minor"``, or ``"major"``.
            
            If ``part`` is a valid version number, it would bump the version
            number to ``part``.
            
        It uses :func:`split_version` to find the version. After bumping, it
        would assign the old version to ``conf["old_version"]`` and the new
        version to ``conf["version"]``.
        """
        import semver

        file = pathlib.Path(f(self.file))
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
    """A simple printer."""
    def __init__(self, *items):
        """
        :arg list items: Items which would be logged.
        """
        self.items = items
        
    def __call__(self):
        """When called, it prints the items to the console with :func:`log`."""
        for item in self.items:
            if isinstance(item, str):
                item = f(item)
            log(item)
        
class Chain:
    """An executor which runs tasks in sequence."""
    def __init__(self, *task_lists):
        """
        :arg list[list] task_lists: Multiple list of tasks.
        
        When the task is a :class:`list`, it would be converted into
        :class:`Chain`::
        
            cute(
                foo = ["echo foo", "echo bar"]
            )
            # equals to
            cute(
                foo = Chain(["echo foo", "echo bar"])
            )
        """
        self.task_lists = task_lists
        
    def __call__(self, *args):
        """It runs all tasks in sequence.
        
        :arg list[str] args: Other arguments would be passed into *each* task.
        """
        for list in self.task_lists:
            for item in list:
                run_task(item, *args)
                
class Throw:
    """An executor which throws errors."""
    def __init__(self, err=None):
        """
        :arg err: The error.
        :type err: str or Exception or None or class
        
        When the task is an instance of :class:`Exception` or a subclass of
        :class:`Exception`, it would be converted into :class:`Throw`::
        
            cute(
                foo = Exception,
                foo2 = Exception("some message")
            )
            # equals to
            cute(
                foo = Throw(Exception),
                foo2 = Throw(Exception("some message"))
            )
        """
        self.err = err
        
    def __call__(self):
        """
        When called, it behaves differently according to the type of ``err``:
        
        * If ``err`` is ``None``, re-raises last error.
        * If ``err`` is an instance of :class:`BaseException`, raises ``err``.
        * If ``err`` is an instance of :class:`str`, raises ``Exception(err)``.
        * If ``err`` is callable, raises ``err()``.
        """
        if not self.err:
            raise # pylint: disable=misplaced-bare-raise
        if isinstance(self.err, BaseException):
            raise self.err
        if isinstance(self.err, str):
            raise Exception(self.err)
        if callable(self.err):
            raise self.err()
            
class Try:
    """An executor which suppresses errors."""
    def __init__(self, *tasks):
        """
        :arg list tasks: The tasks which should be run.
        """
        self.tasks = tasks
        
    def __call__(self, *args):
        """When called, the tasks are executed in sequence. If a task raises
        an error, the error would be logged and continue to the next task.
        
        :arg list[str] args: Other arguments would be sent to each task.
        
        Example::
        
            cute(
                foo = Try(
                    "echo execute and fail && exit 1", # executed
                    "echo execute and fail && exit 1" # executed
                ),
                foo_err = "echo foo failed" # not executed
            )
        """
        for task in self.tasks:
            try:
                run_task(task, *args)
            except Exception as err: # pylint: disable=broad-except
                log(err)

def cute(**tasks):
    """Main entry point.

    Define your tasks as keyword arguments. Those tasks would be assigned to
    :const:`conf` with key ``"tasks"``.
        
    There are some tasks having special effects:

    * ``pkg_name``: When this task is defined:
    
      - The key is removed and inserted into :const:`conf`. This allows you to
        specify ``{pkg_name}`` variable in other tasks.
        
      - The module would try to find the version number from
        ``{pkg_name}/__init__.py`` or ``{pkg_name}/__pkginfo__.py``. If found,
        the filename is inserted to :const:`conf` with key ``"version_file"``,
        and the version is inserted with key ``"version"``.

        See :func:`split_version` for the regular expression matching
        ``__version__``.
        
    Some tasks have a default value:
      
    * ``version``: ``Log("{version}")``. You can run ``cute version`` to log
      the version of ``{pkg_name}`` module.
    * ``bump``: ``Bump("{version_file}")``. You can run ``cute bump 
      [major|minor|patch]`` to bump the version of ``{version_file}``.
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
    
class TaskConverter:
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
    task = task_converter.transform(task)
        
    if not callable(task):
        raise Exception("{task!r} is not callable".format(task=task))

    task(*args)
    
task_converter = TaskConverter()
"""The task converter used by pyXcute.

You can extend the converter like this::

    # let's say you want to convert tasks that start with ``"my:..."`` into
    # ``MyTask``
    
    # create the callable executor
    class MyTask:
        def __init__(self, task):
            self.task = task
        def __call__(self):
            # do something to ``task``...
            
    # create a test function
    def is_my_task(task):
        return isinstance(task, str) and task.startswith("my:")
        
    # prepend them to ``task_converter.matchers`` so that MyTask converter is
    # processed before Cmd converter.
    task_converter.matchers.insert(0, (is_my_task, MyTask))
    
    # the task would be converted automatically
    task_converter.transform("my:this is a custom task")
    # -> MyTask("my:this is a custom task")
"""

@task_converter.add(Task)
def _(task):
    return isinstance(task, str) and task in conf.get("tasks", ())

@task_converter.add(Cmd)
def _(task):
    return isinstance(task, str)
    
@task_converter.add(Chain)
def _(task):
    try:
        iter(task)
    except TypeError:
        return False
    return True
    
@task_converter.add(Throw)
def _(task):
    if isinstance(task, BaseException):
        return True
    if isclass(task) and issubclass(task, BaseException):
        return True
    return False
