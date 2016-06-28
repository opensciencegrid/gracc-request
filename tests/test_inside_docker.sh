#!/bin/sh -xe


# Install all the things
rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
curl -O /etc/yum.repos.d/djw8605-GRACC-epel-7.repo https://copr.fedorainfracloud.org/coprs/djw8605/GRACC/repo/epel-7/djw8605-GRACC-epel-7.repo 
yum -y update

yum -y install python-pip git rabbitmq-server java-1.8.0-openjdk elasticsearch-dsl rpm-build
rpm -Uvh https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/rpm/elasticsearch/2.3.2/elasticsearch-2.3.2.rpm

systemctl start elasticsearch.service
systemctl start rabbitmq-server.service

# Prepare the RPM environment
mkdir -p /tmp/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
cat >> /etc/rpm/macros.dist << EOF
%dist .osg.el${OS_VERSION}
%osg 1
EOF

cp gracc-request/config/gracc-request.spec /tmp/rpmbuild/SPECS
package_version=`grep Version gracc-request/config/gracc-request.spec | awk '{print $2}'`
pushd gracc-request
git archive --format=tar --prefix=gracc-request-${package_version}/ HEAD  | gzip >/tmp/rpmbuild/SOURCES/gracc-request-${package_version}.tar.gz
popd

# Build the RPM
rpmbuild --define '_topdir /tmp/rpmbuild' -ba /tmp/rpmbuild/SPECS/htcondor-ce.spec

yum localinstall -y /tmp/rpmbuild/RPMS/noarch/gracc-request*

systemctl start graccreq.service

# Wait for the overmind to start up
sleep 10
#journalctl -u graccreq.service --no-pager

# Install the test data
curl -O https://nodejs.org/dist/v4.4.4/node-v4.4.4-linux-x64.tar.xz
tar xf node-v4.4.4-linux-x64.tar.xz
export PATH=$PATH:`pwd`/node-v4.4.4-linux-x64/bin
npm install elasticdump -g

git clone https://github.com/djw8605/gracc-test-data.git
pushd gracc-test-data
bash -x ./import.sh
popd

pushd gracc-request
python -m unittest discover tests/unittests "test_*.py"
popd

sleep 1
journalctl -u graccreq.service --no-pager -n 20



