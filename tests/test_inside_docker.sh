#!/bin/sh -xe


# Install all the things
yum install -y python
pip install -r /gracc-request/requirements.txt

# Install and Start overmind
python setup.py install
graccreq -c /gracc-request/tests/gracc-request-test.toml &
overmind_pid=$!

python /gracc-request/tests/test.py

kill $overmind_pid


