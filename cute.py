from xcute import cute, Exc

cute(
	pkg_name = 'xcute',
	test = ['pylint xcute cute setup', 'readme_build'],
	bump_pre = 'test',
	bump_post = ['dist', 'release', 'publish', 'install'],
	dist = 'python setup.py sdist bdist_wheel',
	release = [
		'git add .',
		'git commit -m "Release v{version}"',
		'git tag -a v{version} -m "Release v{version}"'
	],
	publish = [
		'twine upload dist/*{version}*',
		'git push --follow-tags'
	],
	install = 'pip install -e .',
	install_err = 'elevate -c -w pip install -e .',
	readme_build = 
		'python setup.py --long-description > build/long-description.rst && '
		'rst2html --no-raw --exit-status=1 --verbose '
		'build/long-description.rst build/long-description.html',
	readme_build_err = ['readme_show', Exc()],
	readme_show = 'start build/long-description.html',
	readme = 'readme_build',
	readme_post = 'readme_show'
)
