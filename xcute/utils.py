#! python3

from docopt import docopt
from os import makedirs
from pathlib import Path
from send2trash import send2trash
from shutil import copy2
import sys
from natsort import natsorted

def clean():
	doc = """Delete folders and files.
	
Usage:
  x-clean [--source=<dir>] <pattern>...
  
Options:
  -s --source=<dir>  Source directory. [default: .]
"""
	args = docopt(doc)
	src = Path(args["--source"])
	for p in args["<pattern>"]:
		for file in src.glob(p):
			print("delete", file)
			send2trash(str(file))
	
def concat():
	doc = """Concat files and print to stdout. Each file is only printed once.
	
Usage:
  x-cat [--source=<dir>] [--no-line-end] [--ignore=<pattern>]...
        <pattern>...
  
Options:
  -s --source=<dir>      Source directory. [default: .]
  -i --ignore=<pattern>  Ignore file pattern.
  -o --no-line-end       Don't print line end after each file.
"""	
	args = docopt(doc)
	src = Path(args["--source"])
	ignore = args["--ignore"]
	end = "" if args["--no-line-end"] else "\n"
	processed = set()
	for p in args["<pattern>"]:
		for file in natsorted(src.glob(p)):
			if file in processed:
				continue
			processed.add(file)
			if any(file.match(i) for i in ignore):
				continue
			print(file.read_text("utf-8"), end=end)
	
def copy():
	doc = """Copy files. Note that a if pattern matches a folder, the folder
is ignored. Use **/* to copy folder's content.

Usage:
  x-copy [--source=<dir] [--ignore=<pattern>]... <dest_dir> <pattern>...
  
Options:
  -s --source=<dir>      Source directory. [default: .]
  -i --ignore=<pattern>  Ignore file pattern.
"""
	args = docopt(doc)
	src = Path(args["--source"])
	dest = Path(args["<dest_dir>"])
	ignore = args["--ignore"]
	files = set()
	for pattern in args["<pattern>"]:
		files.update(src.glob(pattern))
	if not files:
		print("Patterns doesn't match any file.")
		return
	
	created_parents = set()
	for file in files:
		if file.is_dir():
			continue
		if any(file.match(i) for i in ignore):
			continue
		new_file = dest / file.relative_to(src)
		print("copy", file)
		if new_file.parent not in created_parents:
			makedirs(new_file.parent, exist_ok=True)
			created_parents.add(new_file.parent)
		copy2(file, new_file)
	
def pipe():
	doc = """Read stdin and output to a file. It automatically creates missing
folders.

Usage:
  x-pipe <file>
"""
	args = docopt(doc)
	with open(args["<file>"], "w") as f:
		for line in sys.stdin:
			f.write(line)
	