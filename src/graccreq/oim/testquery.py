#!/usr/bin/python

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from OIMTopology import OIMTopology
import re

outfile = '/var/tmp/testOIMTopology.csv'
header = "#{0},{1},{2},{3},{4}#\n".format(
    'RecordID','ProbeName', 'Raw_SiteName', 'ResourceGroup', 'OIM_SiteName'
)

client = Elasticsearch(['https://fifemon-es.fnal.gov'],
                       use_ssl=True,
                       verify_certs=True,
                       ca_certs='/etc/grid-security/certificates/cilogon-osg.pem',
                       client_cert='gracc_cert/gracc-reports-dev.crt',
                       client_key='gracc_cert/gracc-reports-dev.key',
                       timeout=60)

# client = Elasticsearch('localhost', timeout=60)

results = Search(using=client, index='gracc.osg.raw-2016.08')\
    .query('match_all')

results = results[:1000]
response = results.execute()
responsedict = response.to_dict()

testdict = {}
for item in responsedict['hits']['hits']:
    recordid = item['_source']['RecordId']
    testdict[recordid] = {}
    curdict = testdict[recordid]
    curdict['ProbeName'] = item['_source']['ProbeName']
    curdict['RawSiteName'] = item['_source']['SiteName']

# print testdict

topology = OIMTopology(newfile=True)


successes, failures, parsed = 0, 0, 0
badfqdns = []
badsites = []
outall = ''

for key, item in testdict.iteritems():
    rawsite = item['RawSiteName']
    probename = item['ProbeName']
    probe_fqdn = re.match('.+:(.+)', probename).group(1)

    if probe_fqdn not in badfqdns:
        graccinfodict = topology.get_information_by_fqdn(probe_fqdn)
        if graccinfodict:
            outlist = [key, probename,rawsite,
                       graccinfodict['ResourceGroup'],graccinfodict['Site']
                       ]
            successes += 1
        else:
            badfqdns.append(probe_fqdn)
            if rawsite not in badsites:
                graccinfodict = topology.get_information_by_resource(
                    rawsite)
                if graccinfodict:
                    outlist = [key, probename, rawsite,
                               graccinfodict['ResourceGroup'],
                               graccinfodict['Site']
                               ]
                    successes += 1
                else:
                    failures += 1
                    badsites.append(badsites)
                    continue
    else:
        failures += 1
        continue

    outstr = ','.join(outlist)
    outall += outstr + '\n'
    parsed += 1
    if parsed % 10 == 0:
        parsestring = "Parsed {0} records".format(parsed)
        print parsestring

with open(outfile,'w') as f:
    f.write(header)
    f.write(outall)

print "Successes: {0}, Failures: {1}, Total: {2}".format(successes, failures,
                                                         successes + failures)
