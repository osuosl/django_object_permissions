#!/usr/bin/env python

from setuptools import setup

long_desc = open('README').read()

setup(name='django-object-permissions',
      version="1.4.6",
      description='A method for adding object-level or row-level permissions',
      long_description=long_desc,
      author='Peter Krenesky',
      author_email='kreneskyp@osuosl.org',
      maintainer="Ken Lett",
      maintainer_email="kennric@osuosl.org",
      url='http://code.osuosl.org/projects/object-permissions',
      packages=['object_permissions'],
      include_package_data=True,
      classifiers=[
          "License :: OSI Approved :: MIT License",
          'Framework :: Django',
          'Topic :: Security',
          ],
      )
