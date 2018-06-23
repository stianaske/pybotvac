from setuptools import setup
from pybotvac import __version__

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='pybotvac',
    version=__version__,
    description='Python package for controlling Neato pybotvac Connected vacuum robot',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Stian Askeland',
    author_email='stianaske@gmail.com',
    url='https://github.com/stianaske/pybotvac',
    license='Licensed under the MIT license. See LICENSE file for details',
    packages=['pybotvac'],
    package_dir={'pybotvac': 'pybotvac'},
    package_data={'pybotvac': ['cert/*.crt']}
)
