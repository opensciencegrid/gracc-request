from setuptools import setup, find_packages
from pip.req import parse_requirements
import os

# parse_requirements() returns generator of pip.req.InstallRequirement objects
path=os.path.dirname(os.path.realpath(__file__))
install_reqs = parse_requirements(os.path.join(path, 'requirements.txt'), session=False)
reqs = [str(ir.req) for ir in install_reqs]

setup(name='graccreq',
      version='1.0',
      description='GRACC Request Daemon',
      author_email='dweitzel@cse.unl.edu',
      author='Derek Weitzel',
      url='https://opensciencegrid.github.io/gracc',
      package_dir={'': 'src'},
      packages=['graccreq'],
      install_requires=reqs,
      entry_points= {
            'console_scripts': [
                  'graccreq = graccreq.OverMind:main'
            ]
      }
)
