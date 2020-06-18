import pika
import json
import sys
import logging
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, A
from elasticsearch_dsl.aggs import Composite
from elasticsearch_dsl.query import Q
import traceback
from . import replayer
import dateutil
import copy
import datetime
from graccreq.oim import projects, OIMTopology
import io
from graccreq.correct import Corrections
from . import summary_replayer


def TransferSummaryFactory(msg, parameters, config):
    
    # Start profiling
    if 'General' in config and 'Profile' in config['General'] and config['General']['Profile']:
        logging.debug("Staring profiler")
        import cProfile
        pr = cProfile.Profile()
        pr.enable()
        
    try:
        replayer = TransferSummary(msg, parameters, config)
        replayer.run()
    except Exception as e:
        logging.error(traceback.format_exc())
    
    if 'General' in config and 'Profile' in config['General'] and config['General']['Profile']:
        logging.debug("Stopping profiler")
        import pstats
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        f = open('/tmp/profile.txt', 'a')
        f.write(s.getvalue())
        f.close()
        print(s.getvalue())
        
        
class TransferSummary(summary_replayer.SummaryReplayer):
    def __init__(self, message, parameters, config):
        # Call the init of the SummaryReplayer
        super(TransferSummary, self).__init__(message, parameters, config)
        

    def _queryElasticsearch(self, from_date, to_date, query):
        logging.debug("Connecting to ES")
        client = Elasticsearch(timeout=300)
        
        # For summaries, we only summarize full days, so strip the time from the from & to
        # Round the date up, so we get the entire last day they requested.
        from_date = dateutil.parser.parse(from_date).date()
        to_date = dateutil.parser.parse(to_date).date() + datetime.timedelta(days=1)
        
        logging.debug("Beginning search")
        s = Search(using=client, index=self._config['ElasticSearch']['transfer_index'])
        s = s.filter('range', **{'EndTime': {'from': from_date, 'to': to_date }})
        
        
        # StartTime, VOcorrid, ProjectNameCorrid, ProbeName, CommonName, Protocol, RemoteSite, Status, IsNew, StorageUnit, Grid, DistguishedName
        # Fill in the unique terms and metrics
        unique_terms = [["StartTime", 0], ["VOName", "N/A"], ["ProjectName", "N/A"], ["ProbeName", "N/A"], ["CommonName", "N/A"], \
                        ["Resource_Protocol", "N/A"], ["Status", 0], ["Resource_IsNew", "N/A"], ["Network_storageUnit", "N/A"], \
                        ["Grid", "N/A"], ["DN", "N/A"]]
        
        # Njobs, TransferSize, TransferDuration
        metrics = [["Njobs", 1], ["Network", 0], ["WallDuration", 0]]

        # If the terms are missing, set as "N/A"
        terms_dict = {item[0]: item[1] for item in unique_terms}

        # If the terms are missing, set as "N/A"
        composite_buckets = []
        composite_buckets.append({unique_terms[0][0]: A('date_histogram', field=unique_terms[0][0], interval="day")})
        new_unique_terms = unique_terms[1:]

        # First 3 terms, use composite
        for term in new_unique_terms[:3]:
            composite_buckets.append({term[0]: A('terms', field=term[0], missing_bucket=True)})

        new_unique_terms = new_unique_terms[3:]

        def scan_aggs(search, source_aggs, size=10):
            """
            Helper function used to iterate over all possible bucket combinations of
            ``source_aggs``.  Uses the ``composite`` aggregation under the hood to perform this.
            """
            def run_search(**kwargs):
                s = search[:0]
                curBucket = s.aggs.bucket('comp', 'composite', sources=source_aggs, size=size, **kwargs)
                for term in new_unique_terms:
                    curBucket = curBucket.bucket(term[0], 'terms', field=term[0], missing=term[1], size=(2**31)-1)
                for metric in metrics:
                    curBucket.metric(metric[0], 'sum', field=metric[0], missing=metric[1])
                return s.execute()

            response = run_search()
            while response.aggregations.comp.buckets:
                for b in response.aggregations.comp.buckets:
                    yield b
                if 'after_key' in response.aggregations.comp:
                    after = response.aggregations.comp.after_key
                else:
                    after= response.aggregations.comp.buckets[-1].key
                response = run_search(after=after)

        response = scan_aggs(s, composite_buckets, size=100)


        def recurseBucket(curData, curBucket, index, data):
            """
            Recursively process the buckets down the nested aggregations

            :param curData: Current 
            :param bucket curBucket: A elasticsearch bucket object
            :param int index: Index of the unique_terms that we are processing
            """
            curTerm = new_unique_terms[index][0]

            # Check if we are at the end of the list
            if not curBucket[curTerm]['buckets']:
                # Make a copy of the data
                nowData = copy.deepcopy(curData)
                data.append(nowData)
            else:
                # Get the current key, and add it to the data
                for bucket in curBucket[curTerm]['buckets']:
                    nowData = copy.deepcopy(curData)
                    nowData[curTerm] = bucket['key']
                    if index == (len(new_unique_terms) - 1):
                        # reached the end of the unique terms
                        for metric in metrics:
                            nowData[metric[0]] = bucket[metric[0]].value
                            # Add the doc count
                        nowData["Count"] = bucket['doc_count']
                        data.append(nowData)
                    else:
                        recurseBucket(nowData, bucket, index+1, data)


        for key in response:
            for commonName in key['CommonName']['buckets']:
                data = []
                recurseBucket({"CommonName": commonName['key']}, commonName, 1, data)
                for record in data:
                    record.update(key['key'].to_dict())
                    for term, value in record.items():
                        if value is None and term in terms_dict:
                            record[term] = terms_dict[term]
                    # Convert to iso 8601 date format
                    record['StartTime'] = datetime.datetime.fromtimestamp(record['StartTime'] / 1000).isoformat()
                    yield record
