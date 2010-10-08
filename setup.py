from setuptools import setup
import object_permissions, os

try:
    long_desc = open('README').read()
except IOError:
    long_desc = 'This is a way to add the ability to set and test permissions by model and assign permissions to individual users and groups'

try:
    version = objectpermissions.get_version()
except ImportError:
    version = ''

setup(name='django_object_permissions',
      version=version,
      description='A method for adding object-level or row-level permissions',
      long_description=long_desc,
      author='Peter Krenesky',
      author_email='kreneskyp@osuosl.org',
      url='http://code.osuosl.org/projects/object-permissions',
      packages=['object_permissions'],
      include_package_data=True,
      classifiers=[
          'Framework :: Django',
          'License :: OSI Approved :: MIT Software License',
          'Topic :: Security',
          ],
      )