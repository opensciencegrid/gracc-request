from setuptools import setup, find_packages
import os


setup(name='graccreq',
      version='3.16.0',
      description='GRACC Request Daemon',
      author_email='dweitzel@cse.unl.edu',
      author='Derek Weitzel',
      url='https://opensciencegrid.github.io/gracc',
      package_dir={'': 'src'},
      packages=['graccreq', 'graccreq.oim', 'graccreq.correct'],
      install_requires=['opensearch-py',
      'filelock',
      'pika',
      'python-dateutil',
      'six',
      'toml',
      'urllib3'
      ],
      entry_points= {
            'console_scripts': [
                  'graccreq = graccreq.OverMind:main'
            ]
      }
)
