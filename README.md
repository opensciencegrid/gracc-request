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

The Elasticsearch document for the above configuration could be:

    {
      "_index": "gracc.corrections-0",
      "_type": "project",
      "_id": "AV0ItRBqFBezTrseiOVF",
      "_score": 1,
      "_source": {
        "ProjectName": "osg.mab",
        "CorrectedProjectName": "mab"
      }
    }

In the above example config and document, the correction would look for records which have a `ProjectName == "osg.mab"`, and set the new ProjectName to "mab".

### Regular expression matches

The corrections also have the ability to perform regular expression matches.  The configuration for a regular expression:

    [[Corrections]]
    index = 'gracc.corrections'
    doc_type = 'host_description_regex'
    match_fields = ['Host_description']
    source_field = 'Corrected_OIM_Site'
    dest_field = 'OIM_Site'
    regex = true

And the ES document would look like:

    {
      "_index": "gracc.corrections-0",
      "_type": "host_description_regex",
      "_id": "asldkfj;alksjdf",
      "_score": 1,
      "_source": {
        "Host_description": ".*\.bridges\.psc\.edu",
        "Corrected_OIM_Site": "PSC Bridges",
      }
    }

In this case, it would match the `Host_description` field of the incoming record with the regular expression in the ES record.  If it is a match, then it would set `OIM_Site` to the value in `Corrected_OIM_Site`.



