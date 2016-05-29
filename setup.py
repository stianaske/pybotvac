from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='pybotvac',
    version='0.0.1',
    description='Python package for controlling Neato pybotvac Connected vacuum robot',
    long_description=readme,
    author='Stian Askeland',
    author_email='stianaske@gmail.com',
    url='https://github.com/stianaske/pybotvac',
    license=license,
    packages=['pybotvac'],
    package_dir={'pybotvac': 'pybotvac'},
    package_data={'pybotvac': ['cert/*.crt']}
)
