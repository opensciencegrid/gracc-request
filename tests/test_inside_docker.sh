#!/bin/sh -xe


# Install all the things
rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
yum -y update
yum -y install python-pip

yum -y install rabbitmq-server java-1.8.0-openjdk
rpm -Uvh https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/rpm/elasticsearch/2.3.2/elasticsearch-2.3.2.rpm

systemctl start elasticsearch.service
systemctl start rabbitmq-server.service

cd /gracc-request
pip install -r requirements.txt

# Install and Start overmind
python setup.py install
mkdir -p /etc/gracc/config.d/
cp tests/gracc-request-test.toml /etc/gracc/config.d/gracc-request.toml
cp config/graccreq.service /lib/systemd/system/
systemctl start graccreq.service

# Wait for the overmind to start up
sleep 10
journalctl -u graccreq.service

python tests/test.py

kill $overmind_pid


