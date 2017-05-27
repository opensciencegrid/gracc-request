
FROM opensciencegrid/osg-wn:3.3-el7


RUN yum -y install --enablerepo=osg-contrib,osg-development python-setuptools python2-pika python-elasticsearch-dsl python-dateutil python-toml python-filelock

ADD . /gracc-request
WORKDIR /gracc-request
RUN python setup.py install


run install -d -m 0755 /etc/graccreq/config.d/ && install -m 0744 config/gracc-request.toml /etc/graccreq/config.d/gracc-request.toml

CMD /usr/bin/graccreq

