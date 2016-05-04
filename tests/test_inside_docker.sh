#!/bin/sh -xe


# Install all the things
rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
yum -y update
yum -y install python-pip
cd /gracc-request
pip install -r requirements.txt

# Install and Start overmind
python setup.py install
graccreq -c tests/gracc-request-test.toml &
overmind_pid=$!

python tests/test.py

kill $overmind_pid


