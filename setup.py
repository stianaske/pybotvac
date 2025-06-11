from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="pybotvac",
    version="0.0.28",
    description="Python package for controlling Neato pybotvac Connected vacuum robot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Stian Askeland",
    author_email="stianaske@gmail.com",
    url="https://github.com/stianaske/pybotvac",
    license="Licensed under the MIT license. See LICENSE file for details",
    packages=["pybotvac"],
    package_dir={"pybotvac": "pybotvac"},
    package_data={"pybotvac": ["cert/*.crt"]},
    install_requires=["requests", "requests_oauthlib", "voluptuous"],
)
