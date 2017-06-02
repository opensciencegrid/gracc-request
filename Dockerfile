
FROM opensciencegrid/osg-wn:3.3-el7


RUN cat > /etc/yum.repos.d/djw8605-gracc.repo << EOF
[djw8605-GRACC]
name=Copr repo for GRACC owned by djw8605
baseurl=https://copr-be.cloud.fedoraproject.org/results/djw8605/GRACC/epel-7-$basearch/
type=rpm-md
skip_if_unavailable=True
gpgcheck=1
gpgkey=https://copr-be.cloud.fedoraproject.org/results/djw8605/GRACC/pubkey.gpg
repo_gpgcheck=0
enabled=1
enabled_metadata=1
EOF

RUN yum -y install python-setuptools python2-pika python-elasticsearch-dsl python-dateutil python-toml python-filelock

ADD . /gracc-request
WORKDIR /gracc-request
RUN python setup.py install



RUN install -d -m 0755 /etc/graccreq/config.d/ && install -m 0744 config/gracc-request.toml /etc/graccreq/config.d/gracc-request.toml

CMD /usr/bin/graccreq

