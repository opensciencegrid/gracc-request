
FROM opensciencegrid/osg-wn:3.3-el7

RUN yum -y install --enablerepo=osg-contrib,osg-development gracc-request

