#! python3

from xcute import cute, exc

cute(
	pkg_name = 'xcute',
	lint = 'pylint xcute cute setup',
	test = ['lint', 'readme_build'],
	bump_pre = 'test',
	bump_post = ['clean', 'dist', 'release', 'publish', 'install'],
	clean = 'x-clean build dist',
	dist = 'python setup.py sdist bdist_wheel',
	release = [
		'git add .',
		'git commit -m "Release v{version}"',
		'git tag -a v{version} -m "Release v{version}"'
	],
	publish = [
		'twine upload dist/*',
		'git push --follow-tags'
	],
	install = 'pip install -e .',
	install_err = 'elevate -c -w pip install -e .',
	readme = 'rstpreview README.rst',
	readme_build = [
		'python setup.py --long-description | x-pipe build/ld',
		'rst2html --no-raw --exit-status=2 -r 2 build/ld build/ld.html'
	],
	readme_build_err = ['readme_show', exc],
	readme_show = 'start build/ld.html'
)
