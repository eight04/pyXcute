pyXcute
=======

A small task runner inspired by npm scripts.

Features
--------

* Use it like setuptools.
* Chain tasks with ``_pre``, ``_err``, ``_post``, ``_fin`` suffix.
* A builtin Bump task which can bump version with `semver <https://github.com/k-bx/python-semver>`__.

Install
-------

.. code:: bash

	pip install pyxcute

Usage
-----

Basic
~~~~~

Create a ``cute.py`` file like this:

.. code:: python

	from xcute import cute
	
	cute(
		hello = 'echo hello xcute!'
	)
	
then run:

.. code:: bash

	>cute hello
	hello...
	hello xcute!
	
If you didn't provide the command, it will try to execute ``default`` task.
	
Provide additional arguments:

.. code:: bash

	>cute hello 123
	hello...
	hello xcute! 123

The arguments will be passed into the runner, which is ``xcute.Cmd.__call__`` in this case.

Tasks
~~~~~

It can be a str:

.. code:: python
	
	from xcute import cute
	
	cute(
		hello = 'echo hello'
	)
	
If it is the name of another task, pyxcute will execute that task:

.. code:: python

	from xcute import cute
	
	cute(
		hello = 'world',
		world = 'echo execute world task'
	)
	
use a list:

.. code:: python

	from xcute import cute
	
	cute(
		hello = ['echo task1', 'echo task2']
	)
	
or anything that is callable:

.. code:: python

	from xcute import cute
	
	cute(
		hello = lambda: print('say hello')
	)

Task chain
~~~~~~~~~~
	
Define the workflow with ``_pre``, ``_err``, ``_post``, ``_fin`` suffix:

.. code:: python

	from xcute import cute
	
	cute(
		hello_pre = 'echo _pre runs before the task',
		hello = 'echo say hello',
		hello_err = 'echo _err runs if there is an error in task, i.e, an uncaught exception or non-zero return code',
		hello_post = 'echo _post runs after the task if task successfully returned',
		hello_fin = 'echo _fin always runs after _post, _err just like finally'
	)
	
When a task is involved, it will firstly try to execute _pre task, then the task itself, then the _post task. If the task raised an exception, then it goes to _err task. And finally the _fin task.

Pseudo code:

.. code:: python

	run(name + "_pre")
	try:
		run(name, args)
	except Exception:
		if run(name + "_err") not exist:
			raise
	else:
		run(name + "_post")
	finally:
		run(name + "_fin")

Format string
~~~~~~~~~~~~~

pyXcute will expand format string with ``xcute.conf`` dictionary. Extend it as you need. By the default, it has following keys:

* pkg_name - package name. This is supplied by "pkg_name" task. (i.e. ``cute(pkg_name=...)``)
* date - ``datetime.datetime.now()``.
* tty - a boolean shows if the output is a terminal.
* version - version number. Only available after Bump task or Version task. If you have supplied "pkg_name", PyXcute will try to extract version number from ``{pkg_name}/__init__.py``.
* old_version - version number before bump. Only available after Bump task.
* tasks - a dictionary. This is what you send to ``cute()``.
* init - command name.
* args - additional argument list.
* name - the name of current task.
	
Live example
~~~~~~~~~~~~
	
Checkout `the cute file <https://github.com/eight04/pyXcute/blob/master/cute.py>`__ of pyXcute itself.

xcute.Bump
~~~~~~~~~~

``Bump`` is a builtin task which can bump version like ``__version__ = '0.0.0'``

.. code:: python

	from xcute import cute, Bump
	
	cute(
		bump = Bump('path/to/target/file')
	)
	
then run

.. code:: bash

	cute bump [major|minor|patch|prerelease|build]
	
the argument is optional, default to ``patch``.

Here is the regex used by pyXcute:

.. code:: python

	"__version__ = ['\"]([^'\"]+)"
	
If you doesn't supply ``bump`` task and ``pkg_name`` exists, pyXcute will create a default bump task for you.

.. code:: python

	tasks["bump"] = Bump("{pkg_name}/__init__.py")

xcute.Version
~~~~~~~~~~~~~

This task will extract the version number into ``conf``.

If ``pkg_name`` exists, pyXcute will try to extract version number from ``{pkg_name}/__init__.py`` at start and create a default ``version`` task.

.. code:: python

	tasks["version"] = Log("{version}")

xcute.Exc
~~~~~~~~~

This task will raise an exception.

.. code:: python

	Exc([message])
	
If the message isn't provided, it will reraise the last exception.

xcute.Exit
~~~~~~~~~~

This task will exit the process.

.. code:: python

	Exit([exit_code])
	
Changelog
---------

* 0.3.0 (Jul 21, 2016)

  - Add ``pkg_name`` task.
  - Add default tasks ``bump``, ``version``.

* 0.2.0 (May 14, 2016)

  - Add _fin tag, which represent ``finally`` clause.
  - Add Exc and Exit tasks.

* 0.1.2 (Apr 20, 2016)

  - Move _pre out of try clause.

* 0.1.1 (Apr 20, 2016)

  - Bump dev status.

* 0.1.0 (Apr 20, 2016)

  - First release.

