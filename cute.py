#! python3

import sys

from xcute import cute, Skip

def readme():
    """Live reload readme"""
    from livereload import Server
    server = Server()
    server.watch("README.rst", "py cute.py readme_build")
    server.serve(open_url_delay=1, root="build/readme")
    
cute(
    pkg_name = 'xcute',
    lint = 'pylint xcute cute setup',
    test = [Skip("lint", sys.version_info[:2] != (3, 6)), 'readme_build'],
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
    readme_build = [
        'python setup.py --long-description | x-pipe build/readme/index.rst',
        ('rst2html5 --no-raw --exit-status=1 --verbose '
         'build/readme/index.rst build/readme/index.html')
    ],
    readme_pre = "readme_build",
    readme = readme,
    doc = 'sphinx-autobuild -B -z {pkg_name} docs docs/build'
)
