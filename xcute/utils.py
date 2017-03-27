#! python3

def iter_files(src, patterns, ignores=None, no_subdir=False, no_dir=False):
	"""Iter through files/folders matching glob patterns.
	
	:arg Path src: Source directory.
	:arg list[str] patterns: Glob patterns.
	:arg list[str] ignores: Glob patterns. Ignore matched files/folders.
	
	:arg bool no_subdir: If a and b are matched and a in b.parents, ignore b.
		This option doesn't keep the file order with patterns.
		
	:arg bool no_dir: Ignore folders.
	"""
		
	from ordered_set import OrderedSet
	from natsort import natsorted
	
	processed = OrderedSet()

	def _iter_files(files):
		for file in natsorted(files):
			if no_subdir and processed and processed[-1] in file.parents:
				continue
			if ignores and any(file.match(i) for i in ignores):
				continue
			if no_dir and file.is_dir():
				continue
			if file in processed:
				continue
			processed.add(file)
			yield file
			
	if no_subdir:
		# no_subdir doesn't keep patterns' order
		yield from _iter_files((f for p in patterns for f in src.glob(p)))
	else:
		for pattern in patterns:
			yield from _iter_files(src.glob(pattern))

	if not processed:
		print("No file is matched.")

def clean():
	from pathlib import Path
	from argparse import ArgumentParser
	from send2trash import send2trash
	
	parser = ArgumentParser(description="Delete folders and files.")
	parser.add_argument(
		"-s", dest="src", metavar="<src_dir>", default=".", type=Path,
		help="Source directory.")
	parser.add_argument(
		"patterns", metavar="<pattern>", nargs="+",
		help="Glob pattern matching files/folders.")
	args = parser.parse_args()
	
	for file in iter_files(args.src, args.patterns, no_subdir=True):
		print("delete", file)
		send2trash(str(file))
	
def concat():
	from argparse import ArgumentParser
	from pathlib import Path
	
	parser = ArgumentParser(
		description="Concat files and print to stdout. Each file is only"
			" printed once.")
	parser.add_argument(
		"-s", dest="src", metavar="<src_dir>", default=".", type=Path,
		help="Source directory.")
	parser.add_argument(
		"patterns", metavar="<pattern>", nargs="+",
		help="Glob pattern matching files/folders.")
	parser.add_argument(
		"-i", dest="ignores", metavar="<pattern>", nargs="+",
		help="Glob pattern matching files/folders to be ignored.")
	parser.add_argument(
		"-n", dest="end", action="store_const", const="", default="\n",
		help="Don't print line end after each file.")
	args = parser.parse_args()
	
	for file in iter_files(args.src, args.patterns, ignores=args.ignores,
			no_dir=True):
		print(file.read_text("utf-8"), end=args.end)
	
def copy():
	from argparse import ArgumentParser
	from pathlib import Path
	
	parser = ArgumentParser(
		description="Copy files. Note that a if pattern matches a folder, the"
			" folder is ignored. Use **/* to copy folder's content.")
	parser.add_argument(
		"-s", dest="src", metavar="<src_dir>", default=".", type=Path,
		help="Source directory.")
	parser.add_argument(
		"-i", dest="ignores", metavar="<pattern>", nargs="+",
		help="Glob pattern matching files/folders to be ignored.")
	parser.add_argument(
		"dest", metavar="<dest_dir>", type=Path, help="Destination directory.")
	parser.add_argument(
		"patterns", metavar="<pattern>", nargs="+",
		help="Glob pattern matching files/folders.")
	args = parser.parse_args()
	
	from shutil import copy2
	from os import makedirs
	
	created_parents = set()
	for file in iter_files(args.src, args.patterns, ignores=args.ignores,
			no_dir=True):
		new_file = args.dest / file.relative_to(args.src)
		print("copy", file)
		if new_file.parent not in created_parents:
			makedirs(new_file.parent, exist_ok=True)
			created_parents.add(new_file.parent)
		copy2(file, new_file)
	
def pipe():
	from argparse import ArgumentParser
	from pathlib import Path

	parser = ArgumentParser(
		description="Read stdin and output to a file. It automatically creates"
			" missing folders.")
	parser.add_argument(
		"dest", metavar="<dest_file>", type=Path,
		help="Destination file.")
	args = parser.parse_args()
		
	import sys
	
	with args.dest.open("w") as f:
		for line in sys.stdin:
			f.write(line)
