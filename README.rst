pyXcute
=======

.. image:: https://api.codacy.com/project/badge/Grade/6ffe1c58a9f7404293f870a5183d8ad8    
  :target: https://www.codacy.com/app/eight04/pyXcute?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=eight04/pyXcute&amp;utm_campaign=Badge_Grade

A small task runner inspired by npm scripts.

Features
--------

* Use it like setuptools.
* Chain tasks with ``_pre``, ``_err``, ``_post``, ``_fin`` suffix.
* A builtin Bump task which can bump version with `semver <https://github.com/k-bx/python-semver>`_.

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
	
"hello" is the task to run. If ``cute.py`` is executed without a task name, it will run "default" task.
	
(If you get a "not a command" error, see `How do I make Python scripts executable? <https://docs.python.org/3/faq/windows.html#how-do-i-make-python-scripts-executable>`_)
	
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
	
If it match the name of another task, pyxcute will execute that task:

.. code:: python

	from xcute import cute
	
	cute(
		hello = 'world',
		world = 'echo execute world task'
	)
	
Use a list:

.. code:: python

	from xcute import cute
	
	cute(
		hello = ['echo task1', 'echo task2']
	)
	
Or anything that is callable:

.. code:: python

	from xcute import cute
	
	cute(
		hello = lambda: print('say hello')
	)
  
Actually, when you assign a non-callable as a task, pyxcute converts it into a callable according to its type. See `xcute.Cmd`_, `xcute.Chain`_, `xcute.Throw`_., and `xcute.Task`_

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

pyXcute expands format string with `xcute.conf`_ dictionary when the task is executed:

.. code:: python

  from xcute import conf, cute
  
  conf["my_name"] = "world"
  
  def edit_conf():
    conf["my_name"] = "bad world"

  cute(
    hello_pre = edit_conf,
    hello = "echo hello {my_name}"
  )
  
.. code:: bash

  > cute hello
  hello_pre...
  hello...
  hello bad world
  
Cross-platform utils
--------------------

There are some CLI utils inspired by `npm-build-tools <https://www.npmjs.com/package/npm-build-tools>`_, including:

* x-clean
* x-cat
* x-copy
* x-pipe

Run each ``-h`` help screen to see the description.

Live example
------------
	
Checkout `the cute file <https://github.com/eight04/pyXcute/blob/master/cute.py>`_ of pyXcute itself.

API reference
-------------

xcute.conf
~~~~~~~~~~

A dictionary used to format string. By the default, it has following keys:

* pkg_name - package name. See `xcute.cute`_.
* date - ``datetime.datetime.now()``.
* tty - a boolean shows if the output is a terminal.
* version - version number. Available after Bump task. Also see pkg_name section in `xcute.cute`_.
* old_version - version number before bump. Only available after Bump task.
* tasks - a dictionary. This is what you send to ``cute()``.
* curr_task - str. The name of current task.

xcute.cute
~~~~~~~~~~

.. code:: python

  cute(**tasks)

The entry point.

Here are some special tasks:

* pkg_name - when this key is found in tasks, the key is removed and inserted into the ``conf`` dictionary.

  Then, ``cute()`` tries to find version number from ``{pkg_name}/__init__.py``, ``{pkg_name}/__pkginfo__.py``. If found, the filename is added to ``conf["version_file"]``, and the version is added to ``conf["version"]``.
  
  The regex used to match version number is decribed at ``xcute.split_version``.
  
* version - if not provided, pyxcute uses ``Log("{version}")`` as default.
* bump - if not provided, pyxcute uses ``Bump("{version_file}")`` as default.

xcute.exc
~~~~~~~~~

.. code:: python

  exc(message=None)
  
Raise an exception. It reraises the last error if message is not provided.

.. code:: python
  
  from xcute import cute, exc

  cute(
    ...
    task_err = ["handle error...", exc]
  )

xcute.f
~~~~~~~

.. code:: python

  f(string)
  
Expand string with xcute.conf dictionary.

xcute.log
~~~~~~~~~

.. code:: python

  log(items)
  
A print function, but only works if ``conf["tty"] == False``.

xcute.noop
~~~~~~~~~~

.. code:: python

  noop(*args, **kwargs)
  
A noop.

xcute.split_version
~~~~~~~~~~~~~~~~~~~

.. code:: python

  split_version(text)

Split text into a ``(left, verion, right)`` tuple.

The regex pattern used to find version:

.. code:: python

	"__version__ = ['\"]([^'\"]+)"	

xcute.Bump
~~~~~~~~~~

``Bump`` task can bump version number in a file, using `xcute.split_version`_ and `semver`_.

.. code:: python

	from xcute import cute, Bump
	
	cute(
		bump = Bump('path/to/target/file')
	)
	
then run

.. code:: bash

	cute bump [major|minor|patch|prerelease|build]
	
the argument is optional, default to ``patch``.

xcute.Chain
~~~~~~~~~~~

This task would run each task inside a task list.

.. code:: python

  Chain(*task_list)
  
Tasks are converted to Chain if they are iterable.

xcute.Cmd
~~~~~~~~~

This task is used to run shell command.

.. code:: python

  Cmd(*shell_command)
  
Tasks are converted to Cmd if they are str.

xcute.Log
~~~~~~~~~

A wrapper to ``print``. It is useless if you can just ``"echo something"``.

.. code:: python

  Log(*text)
  
xcute.Task
~~~~~~~~~~

This task executes another task.

.. code:: python

  Task(task_name)
  
Tasks are converted to Task if they are keys of tasks dictionary.
  
xcute.Throw
~~~~~~~~~~~

This task throws error.

.. code:: python

  Throw()
  Throw(error)
  Throw(exc_cls, message=None)
  
1. Reraise last error.
2. Raise the error.
3. Raise ``exc_cls(message)``

Tasks are converted to Throw if they are subclass or instance of BaseException.
  
xcute.Try
~~~~~~~~~

This task suppress exception.

.. code:: python

  Try(*task)
  
Changelog
---------

* Next

  - Switch to setup.cfg.
  - Add log, exc, noop, Throw, Try.
  - *Drop Exc, Exit.*
  - Add ``x-*`` utils.

* 0.3.1 (Mar 23, 2017)

  - Find version from ``{pkg_name}/__pkginfo__.py``.

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

