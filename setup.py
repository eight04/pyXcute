#! python3

from setuptools import setup
from os import path

import re

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
def read(file):
	with open(path.join(here, file), encoding='utf-8') as f:
		content = f.read()
	return content
	
def find_version(file):
	return re.search(r"__version__ = (\S*)", read(file)).group(1).strip("\"'")
	
setup(
	name="pyxcute",
	version=find_version("xcute/__init__.py"),
	description="A small task runner inspired from npm",
	long_description=read("README.rst"),
	author='eight',
	author_email='eight04@gmail.com',
	url='https://github.com/eight04/pyXcute',
	packages=["xcute"],
	install_requires=["semver>=2.4.1,<3"],
	# See https://pypi.python.org/pypi?%3Aaction=list_classifiers
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Natural Language :: Chinese (Traditional)',
		'Programming Language :: Python :: 3.5'
		'Topic :: Software Development :: Libraries :: Python Modules',
		'Topic :: Software Development :: Build Tools'
	],
	license='MIT',
	keywords='run task runner execute bump bumper build tool npm'
)
