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
	readme = 'python setup.py --long-description > %temp%/ld && rst2html --no-raw %temp%/ld %temp%/ld.html && start %temp%/ld.html'
)
