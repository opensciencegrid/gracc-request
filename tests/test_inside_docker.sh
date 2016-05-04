#!/bin/sh -xe


# Install all the things
rpm -iUvh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-5.noarch.rpm
yum -y update
yum -y install python-pip
pip install -r /gracc-request/requirements.txt

# Install and Start overmind
python setup.py install
graccreq -c /gracc-request/tests/gracc-request-test.toml &
overmind_pid=$!

python /gracc-request/tests/test.py

kill $overmind_pid


