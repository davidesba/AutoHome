#! /usr/bin/env python
import io
import re
from setuptools import setup, find_packages


def get_version_from_debian_changelog():
    with io.open('debian/changelog', encoding='utf8') as stream:
        return re.search(r'\((.+)\)', next(stream)).group(1)


setup(
    name='auto-home',
    version=get_version_from_debian_changelog(),
    author='David Burgos',
    include_package_data=True,
    author_email='davidesba@gmail.com',
    url='https://github.com/davidesba/AutoHome',
    description='Service to control home automation with HomeKit',
    license='MIT',
    packages=find_packages()
)
