pyXcute
=======

.. image:: http://readthedocs.org/projects/pyxcute/badge/?version=latest
  :target: http://pyxcute.readthedocs.io/en/latest/?badge=latest
  :alt: Documentation Status

.. image:: https://github.com/eight04/pyXcute/actions/workflows/build.yml/badge.svg
  :target: https://github.com/eight04/pyXcute/actions/workflows/build.yml
  :alt: .github/workflows/build.yml

A small task runner inspired by npm scripts.

Features
--------

* Use it like setuptools.
* Chain tasks with ``_pre``, ``_err``, ``_post``, ``_fin`` suffix.
* A builtin Bump task which can bump version with `semver <https://github.com/k-bx/python-semver>`_.
* A small set of cross-platform CLI utils.

Installation
------------

From `pypi <https://pypi.org/project/pyxcute/>`__

.. code:: bash

	pip install pyxcute

Usage
-----

Basic
~~~~~

Create a ``cute.py`` file:

.. code:: python

  from xcute import cute
  
  cute(
    hello = 'echo hello xcute!'
  )
	
then run:

.. code:: bash

  $ cute hello
  > Task: hello
  > Cmd: echo hello xcute!
  hello xcute!
	
..
  
  If you got a "not a command" error, see `How do I make Python scripts executable? <https://docs.python.org/3/faq/windows.html#how-do-i-make-python-scripts-executable>`_)

"hello" is the name of the task that should be executed. If ``cute.py`` is executed without a task name, it will run the "default" task.
	
Provide additional arguments:

.. code:: bash

  $ cute hello 123
  > Task: hello
  > Cmd: echo hello xcute! 123
  hello xcute! 123

The arguments will be passed into the executor, which is ``xcute.Cmd.__call__`` in this case.

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
    hello = 'world', # execute "world" task when "hello" task is executed
    world = 'echo I am world task'
  )
	
Use a list:

.. code:: python

  from xcute import cute
  
  cute(
    hello = ['echo task1', 'echo task2']
  )
  
Using an Exception would make the task fail:

.. code:: python

  from xcute import cute
  cute(
    hello = Exception("error message")
  )
	
Use anything that is callable:

.. code:: python

  from xcute import cute

  cute(
    hello = lambda: print('say hello')
  )
  
Actually, when you assign a non-callable value as a task, pyXcute converts it into a callable according to its type.

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
	
When a task is executed, the task runner try to execute ``_pre`` task first, then the task itself, then the ``_post`` task. If the task raised an exception, then it goes to the ``_err`` task. ``_fin`` task would be executed whenever the task failed or not.

Pseudo code:

.. code:: python

	run(name + "_pre")
	try:
		run(name, args)
	except Exception:
		run(name + "_err")
	else:
		run(name + "_post")
	finally:
		run(name + "_fin")

Format string
~~~~~~~~~~~~~

pyXcute expands the command string with ``xcute.conf`` dictionary. The expansion is happened at run-time:

.. code:: python

  from xcute import conf, cute
  
  conf["my_name"] = "world"
  
  def change_my_name():
    conf["my_name"] = "bad world"

  cute(
    hello = [
      "echo hello {my_name}",
      change_my_name,
      "echo hello {my_name}"
    ]
  )
  
.. code:: bash

  $ cute hello
  > Task: hello
  > Cmd: echo hello world
  hello world
  > Cmd: echo hello bad world
  hello bad world
  
Cross-platform utils
--------------------

There are some CLI utils inspired by `npm-build-tools <https://www.npmjs.com/package/npm-build-tools>`_, including:

* x-clean
* x-cat
* x-copy
* x-pipe

Run each command with ``-h`` to see the help message.

Live example
------------
	
Checkout `the cute file <https://github.com/eight04/pyXcute/blob/master/cute.py>`_ of pyXcute itself.

Documentation
-------------

http://pyxcute.readthedocs.io/en/latest/
  
Changelog
---------

* 0.8.0 (Feb 4, 2024)

  - Change: drop natsort, implement filename sorting by ourselves.

* 0.7.0 (Oct 22, 2023)

  - Change: now we only test pyxcute on Python>=3.7.
  - Add: ``cfg`` argument in ``Bump``.

* 0.6.0 (Nov 1, 2019)

  - Add: ``LiveReload``.

* 0.5.2 (Jun 14, 2018)

  - Add: support ``bumper`` argument in ``Bump``.
  - Add: support Python 3.4. Drop ``subprocess32``.

* 0.5.1 (May 12, 2018)

  - Add: ``conf["py"]`` variable.

* 0.5.0 (May 11, 2018)

  - Add: support Python 2.
  - Add: documentation.
  - Add: ``Skip``, ``run_task``, ``task_converter``.
  - **Add: `Bump` task now update the version number inside `setup.cfg`.**
  - Fix: ``Cmd`` task failed on Unix due to ``shell=True`` and passing ``args`` as a list.
  - **Change: the command of `Cmd` is now logged. The log message is also changed.**
  - **Drop: `noop`.**

* 0.4.1 (Apr 3, 2017)

  - Better description for x-clean.
  - Fix broken pipe error in x-pipe.

* 0.4.0 (Mar 28, 2017)

  - Switch to setup.cfg.
  - Add log, exc, noop, Throw, Try.
  - **Drop Exc, Exit.**
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

