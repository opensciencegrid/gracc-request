import pika
import json
import sys
import logging
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Q
import traceback
import replayer
import dateutil
import copy
import datetime
from graccreq.oim import projects, OIMTopology
import StringIO
from graccreq.correct import Corrections
import summary_replayer


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
    except Exception, e:
        logging.error(traceback.format_exc())
    
    if 'General' in config and 'Profile' in config['General'] and config['General']['Profile']:
        logging.debug("Stopping profiler")
        import pstats
        pr.disable()
        s = StringIO.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        f = open('/tmp/profile.txt', 'a')
        f.write(s.getvalue())
        f.close()
        print s.getvalue()
        
        
class TransferSummary(summary_replayer.SummaryReplayer):
    def __init__(self, message, parameters, config):
        # Initialize the parent
        super(SummaryReplayer, self).__init__(message, parameters, config)
        

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
        s = s.query('bool', must=[Q('match', ResourceType=self._config['ElasticSearch']['transfer_type'])])
        
        
        # StartTime, VOcorrid, ProjectNameCorrid, ProbeName, CommonName, Protocol, RemoteSite, Status, IsNew, StorageUnit, Grid, DistguishedName
        # Fill in the unique terms and metrics
        unique_terms = [["StartTime", 0], ["VOName", "N/A"], ["ProjectName", "N/A"], ["ProbeName", "N/A"], ["CommonName", "N/A"], \
                        ["Resource_Protocol", "N/A"], ["Resource_Destination", "N/A"], ["Status", 0], ["Resource_IsNew", "N/A"], ["Network_storageUnit", "N/A"], \
                        ["Grid", "N/A"], ["DN", "N/A"], ["Resource_Source", "N/A"]]
        
        # Njobs, TransferSize, TransferDuration
        metrics = ["Njobs", "Network", "WallDuration"]

        # If the terms are missing, set as "N/A"
        curBucket = s.aggs.bucket(unique_terms[0][0], 'date_histogram', field=unique_terms[0][0], interval="day")
        new_unique_terms = unique_terms[1:]

        for term in new_unique_terms:
        	curBucket = curBucket.bucket(term[0], 'terms', field=term[0], missing=term[1], size=(2**31)-1)

        for metric in metrics:
        	curBucket.metric(metric, 'sum', field=metric)
            
        response = s.execute()
            
        
        def recurseBucket(curData, curBucket, index, data):
            """
            Recursively process the buckets down the nested aggregations
            
            :param curData: Current 
            :param bucket curBucket: A elasticsearch bucket object
            :param int index: Index of the unique_terms that we are processing
            """
            curTerm = unique_terms[index][0]

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
                    if index == (len(unique_terms) - 1):
                        # reached the end of the unique terms
                        for metric in metrics:
                            nowData[metric] = bucket[metric].value
                            # Add the doc count
                        nowData["Count"] = bucket['doc_count']
                        data.append(nowData)
                    else:
                        recurseBucket(nowData, bucket, index+1, data)


        	
        
        # We only want to hold onto 1 day's worth of summaries
        print len(response.aggregations['StartTime']['buckets'])
        for day in response.aggregations['StartTime']['buckets']:
            data = []
            recurseBucket({"StartTime": day['key_as_string']}, day, 1, data)
            yield data
    

        
        # Aggregate on njobs, WallDuration, CpuUserDuration, CpuSystemDuration
        # Or, unique keys on EndTime (day), VO, ProjectName, CommonName, DN, ResourceType, HostDescription, ApplicationExitCode, Grid, Cores
        
