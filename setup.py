import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

REQUIREMENTS = [
    'pyfxa',
    'aioredis',
    'websockets'
]

ENTRY_POINTS = {
    'paste.app_factory': [
        'main = readinglist:main',
    ]}


setup(name='remote-worker',
      version='0.1.dev0',
      description='Gecko Cloud Remote Worker',
      long_description=README,
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 3 :: Only",
          "Topic :: Internet :: WWW/HTTP",
      ],
      keywords="web services",
      author='Mozilla Services',
      author_email='services-dev@mozilla.com',
      url='https://github.com/mozilla-services/remote-worker-server',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=REQUIREMENTS,
      entry_points=ENTRY_POINTS)
