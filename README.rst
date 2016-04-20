pyXcute
=======

A small task runner inspired from npm.

Features
--------

* Interface like setuptools.
* Chain tasks with ``_pre``, ``_err``, ``_post`` suffix.
* A builtin Bump task which can bump version with `semver <https://github.com/k-bx/python-semver>`__.

Install
-------

::

	pip install pyxcute

Usage
-----

Create a ``cute.py`` file

::

	from xcute import cute, Bump

	cute(
		test = 'setup check -r',
		bump_pre = 'test',
		bump = Bump('xcute/__init__.py'),
		bump_post = ['dist', 'release', 'publish', 'install'],
		dist = 'python setup.py sdist bdist_wheel',
		release = [
			'git add .',
			'git commit -m "Release v{version}"',
			'git tag v{version}'
		],
		publish = [
			'twine upload dist/*{version}*',
			'git push --follow-tags'
		],
		install = 'pip install -e .',
		install_err = 'elevate -c -w pip install -e .',
		readme = 'python setup.py --long-description > %temp%/ld && rst2html %temp%/ld %temp%/ld.html && start %temp%/ld.html'
	)
	
Run it

::

	cute <your_command> <options>...

Changelog
---------

* Version 0.1.0 (Apr 20, 2016)

  - First release.

