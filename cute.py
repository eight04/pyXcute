#! python3

import sys

from xcute import cute, Skip, LiveReload
    
cute(
    pkg_name = 'xcute',
    lint = 'pylint xcute cute setup',
    test = [Skip("lint", sys.version_info < (2,)), 'python test.py', 'readme_build'],
    bump_pre = 'test',
    bump_post = ['clean', 'dist', 'release', 'publish', 'install'],
    clean = 'x-clean build dist *.egg-info',
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
        ('rst2html5.py --no-raw --exit-status=1 --verbose '
         'build/readme/index.rst build/readme/index.html')
    ],
    readme_pre = "readme_build",
    readme = LiveReload("README.rst", "readme_build", "build/readme"),
    doc_build = "sphinx-build docs build/docs",
    doc_pre = "doc_build",
    doc = LiveReload(["{pkg_name}", "docs"], "doc_build", "build/docs")
)
