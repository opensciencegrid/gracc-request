GRACC Request Daemon
====================

This daemon listens and responds to requests for replays on a AMQP queue.

[![Build Status](https://travis-ci.org/opensciencegrid/gracc-request.svg?branch=master)](https://travis-ci.org/opensciencegrid/gracc-request)

## Installing

It is easy to install the GRACC Request Daemon with virtualenv

    virtualenv gracc-test
    . gracc-test/bin/activate
    pip install -r requirements.txt
    python setup.py install


## Docker Installation

A docker image with gracc-request installed in available as opensciencegrid/gracc-request.  


## Corrections

The configuration for a correction is

    [[Corrections]]
    index = 'gracc.corrections'
    doc_type = 'project'
    match_fields = ['ProjectName']
    source_field = 'CorrectedProjectName'
    dest_field = 'ProjectName'

Each correction is required to have the above fields.  You can imagine the logic as:

* If the `match_fields` match the incoming record
* Take the value in `source_field` and put it in `dest_field`

The corrections are stored in Elasticsearch.


