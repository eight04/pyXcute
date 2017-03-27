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
		
def base_parser(description):
	from pathlib import Path
	from argparse import ArgumentParser
	
	parser = ArgumentParser(description=description)
	parser.add_argument(
		"-s", dest="src", metavar="<src_dir>", default=".", type=Path,
		help="Source directory.")
	parser.add_argument(
		"-i", dest="ignores", metavar="<pattern>", action="append",
		help=
			"Glob pattern matching files/folders to be ignored. This option "
			"can be used multiple times.")
	parser.add_argument(
		"patterns", metavar="<pattern>", nargs="+",
		help="Glob pattern matching files/folders.")
		
	def files(**options):
		yield from iter_files(parse().src, parse().patterns,
			ignores=parse().ignores, **options)
			
	ARGS = None
	def parse():
		nonlocal ARGS
		if not ARGS:
			ARGS = parser.parse_args()
		return ARGS
		
	return parser.add_argument, parse, files

def clean():
	from send2trash import send2trash
	
	_add, _parse, files = base_parser("Delete folders and files recursively.")
	
	for file in files(no_subdir=True):
		print("delete", file)
		send2trash(str(file))
	
def concat():
	add, parse, files = base_parser(
		"Concat files and print to stdout. Each file is only "
		"printed once.")
		
	add("-n", dest="end", action="store_const", const="", default="\n",
		help="Don't print line end after each file.")
		
	args = parse()
	
	for file in files(no_dir=True):
		print(file.read_text("utf-8"), end=args.end)
	
def copy():
	from pathlib import Path
	from shutil import copy2
	from os import makedirs
	
	add, parse, files = base_parser(
		"Copy files. Note that if pattern matches a folder, the"
		" folder is ignored. Use **/* to match folder's content.\n\n"
		"Missing folders are automatically created.")
		
	add("dest", metavar="<dest_dir>", type=Path, help="Destination directory.")
	
	args = parse()
	
	created_parents = set()
	for file in files(no_dir=True):
		new_file = args.dest / file.relative_to(args.src)
		print("copy", file, "to", new_file)
		if new_file.parent not in created_parents:
			makedirs(new_file.parent, exist_ok=True)
			created_parents.add(new_file.parent)
		copy2(file, new_file)
	
def pipe():
	from argparse import ArgumentParser
	from pathlib import Path
	from sys import stdin
	from os import makedirs

	parser = ArgumentParser(
		description="Read stdin and output to a file. Missing folders are "
			"automatically created.")
	parser.add_argument(
		"dest", metavar="<dest_file>", type=Path,
		help="Destination file.")
	args = parser.parse_args()
		
	makedirs(args.dest.parent, exist_ok=True)
	with args.dest.open("w") as f:
		for line in stdin:
			f.write(line)
