#!/usr/bin/env python

from setuptools import setup

long_desc = open('README').read()

setup(name='django-object-log',
      version="0.7",
      description='A method for logging user actions on models',
      long_description=long_desc,
      author='Peter Krenesky',
      author_email='peter@osuosl.org',
      maintainer="Corbin Simpson",
      maintainer_email="simpsoco@osuosl.org",
      url='http://code.osuosl.org/projects/django-object-log',
      packages=['object_log'],
      include_package_data=True,
      classifiers=[
          "License :: OSI Approved :: MIT License",
          'Framework :: Django',
          ],
      )
