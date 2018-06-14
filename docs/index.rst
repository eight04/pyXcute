.. currentmodule:: xcute

pyXcute API reference
=====================

A small task runner inspired by npm scripts.

Usage/examples can be founded in `README <https://github.com/eight04/pyXcute>`_.

Constants
---------

.. autodata:: conf
  :annotation: = dict()
  
.. autodata:: task_converter
  :annotation: = TaskConverter()

Functions
---------

.. autofunction:: cute

.. autofunction:: f

.. autofunction:: log

.. autofunction:: run_task

.. autofunction:: split_version

.. autofunction:: semver_bumper

Classes
-------

.. autoclass:: Bump
  :members: __call__
  
.. autoclass:: Chain
  :members: __call__

.. autoclass:: Cmd
  :members: __call__
  
.. autoclass:: Log
  :members: __call__
  
.. autoclass:: Skip
  :members: __call__
  
.. autoclass:: Throw
  :members: __call__
  
.. autoclass:: Try
  :members: __call__
