from setuptools import setup, find_packages
import os


setup(name='graccreq',
      version='3.0.1',
      description='GRACC Request Daemon',
      author_email='dweitzel@cse.unl.edu',
      author='Derek Weitzel',
      url='https://opensciencegrid.github.io/gracc',
      package_dir={'': 'src'},
      packages=['graccreq', 'graccreq.oim', 'graccreq.correct'],
      install_requires=['elasticsearch',
      'elasticsearch-dsl',
      'pika',
      'python-dateutil',
      'six',
      'toml',
      'urllib3',
      'wsgiref'
      ],
      entry_points= {
            'console_scripts': [
                  'graccreq = graccreq.OverMind:main'
            ]
      }
)
