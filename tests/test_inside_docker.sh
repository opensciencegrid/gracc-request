#!/bin/sh -xe


# Install all the things
rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
yum -y update
yum -y install python-pip
pip install -r /gracc-request/requirements.txt

# Install and Start overmind
python /gracc-request/setup.py install
graccreq -c /gracc-request/tests/gracc-request-test.toml &
overmind_pid=$!

python /gracc-request/tests/test.py

kill $overmind_pid


