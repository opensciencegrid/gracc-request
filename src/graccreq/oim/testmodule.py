#!/usr/bin/python

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from OIMTopology import OIMTopology
from datetime import datetime
from os import path
import re


results_count = 1000

outfile = '/var/tmp/testOIMTopology.csv'
statistics = '/var/tmp/stats.csv'
successes, failures, parsed = 0, 0, 0

header = "#{0},{1},{2},{3},{4}#\n".format(
    'RecordID','ProbeName', 'Raw_SiteName', 'ResourceGroup', 'OIM_SiteName'
)
statsheader = '#{0},{1},{2},{3},{4}#\n'.format('Date',
                                             'Successes',
                                             'Failures',
                                             'Total',
                                             'Percent Success')



def get_gracc_results(numresults):
    client = Elasticsearch(['https://fifemon-es.fnal.gov'],
                           use_ssl=True,
                           verify_certs=True,
                           ca_certs='/etc/grid-security/certificates/cilogon-osg.pem',
                           client_cert='gracc_cert/gracc-reports-dev.crt',
                           client_key='gracc_cert/gracc-reports-dev.key',
                           timeout=60)

    # client = Elasticsearch('localhost', timeout=60)

    results = Search(using=client, index='gracc.osg.raw-2016.08') \
        .query('match_all')

    results = results[:numresults]
    response = results.execute()
    responsedict = response.to_dict()

    testdict = {}
    for item in responsedict['hits']['hits']:
        recordid = item['_source']['RecordId']
        testdict[recordid] = {}
        curdict = testdict[recordid]
        curdict['ProbeName'] = item['_source']['ProbeName']
        curdict['SiteName'] = item['_source']['SiteName']
        curdict['VOName'] = item['_source']['VOName']

    return testdict


def compare_to_OIM(graccdict):
    global successes, failures, parsed

    outall = ''
    topology = OIMTopology(newfile=True)

    for key, item in graccdict.iteritems():
        OIM_dict = topology.generate_dict_for_gracc(item)
        if OIM_dict:
            successes += 1
            outlist = [key, item['ProbeName'], item['SiteName'],
                       OIM_dict['ResourceGroup'], OIM_dict['Site']
                       ]
        else:
            failures += 1
        parsed += 1

        outstr = ','.join(outlist)
        outall += outstr + '\n'
        if parsed % 10 == 0:
            parsestring = "Parsed {0} records".format(parsed)
            print parsestring

    return outall


def write_to_stats(mode, data):
    global statistics, statsheader
    with open(statistics, mode) as f:
        if re.search('r', mode):
            if len(f.readlines()) == 0:
                f.write(statsheader)
            f.write('{0},{1},{2},{3},{4}\n'.format(datetime.now(),
                                                   *data))
        else:
            f.write(statsheader)
            f.write('{0},{1},{2},{3},{4}\n'.format(datetime.now(),
                                               *data))
    return


def main():
    global results_count
    gracc_dict = get_gracc_results(results_count)
    output = compare_to_OIM(gracc_dict)

    statslist = [successes, failures, successes + failures,
                 float(100 * successes / (successes+ failures))]

    print "Successes: {0}, Failures: {1}, Total: {2}, Percent Success: {3}"\
        .format(*statslist)

    with open(outfile,'w') as f:
        f.write(header)
        f.write(output)

    if path.exists(statistics):
        write_to_stats('r+', statslist)
    else:
        write_to_stats('w', statslist)


if __name__ == '__main__':
    main()

