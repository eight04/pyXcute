.. currentmodule:: apng

pyXcute API reference
=====================

A small task runner inspired by npm scripts.

Usage/examples can be founded in `README <https://github.com/eight04/pyXcute>`_.

Functions
---------

.. autofunction:: parse_chunks

.. autofunction:: make_chunk

Classes
-------

.. autoclass:: PNG
  :members: open, open_any, from_bytes, to_bytes, save

.. autoclass:: FrameControl
  :members: from_bytes, to_bytes

.. autoclass:: APNG
  :members: open, append, append_file, from_bytes, to_bytes, from_files, save
