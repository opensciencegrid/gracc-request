import pika
import json
import sys
import logging
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import traceback
import replayer
import dateutil
import copy

def SummaryReplayerFactory(msg, parameters):
    # Create the raw replayer class
    #print "Creating raw replayer"
    try:
        replayer = SummaryReplayer(msg, parameters)
        replayer.run()
    except Exception, e:
        logging.error(traceback.format_exc())
        
        
class SummaryReplayer(replayer.Replayer):
    def __init__(self, message, parameters):
        super(SummaryReplayer, self).__init__(message, parameters)

        
    def run(self):
        logging.debug("Beggining run of SummaryReplayer")
        self.createConnection()
        
        
        # Send start message to control channel, if requested
        self.sendControlMessage({'status': 'ok', 'stage': 'starting'})

        # Query elsaticsearch and send the data to the destination
        logging.info("Sending response to %s with routing key %s" % (self.msg['destination'], self.msg['routing_key']))
        try:
            for day in self._queryElasticsearch(self.msg['from'], self.msg['to'], None):
                for record in day:
                    self.sendMessage(json.dumps(record))
        except Exception, e:
            logging.error("Exception caught in query ES: %s" % str(e))
            logging.error(traceback.format_exc())
            raise e
            
        
        self.sendControlMessage({'status': 'ok', 'stage': 'finished'})
        
        self.conn.close()


    def on_return(self, channel, method, properties, body):
        sys.stderr.write("Got returned message\n")
        
    def _queryElasticsearch(self, from_date, to_date, query):
        logging.debug("Connecting to ES")
        client = Elasticsearch(timeout=300)
        
        # For summaries, we only summarize full days, so strip the time from the from & to
        from_date = dateutil.parser.parse(from_date).date()
        to_date = dateutil.parser.parse(to_date).date()
        
        logging.debug("Beginning search")
        s = Search(using=client, index='gracc.osg.raw-*')
        s = s.filter('range', **{'EndTime': {'from': from_date, 'to': to_date }})
        
        # Fill in the unique terms and metrics
        unique_terms = ["EndTime", "VOName", "Processors", "ResourceType", "CommonName", "Host_description", "Resource_ExitCode", "Grid"]
        metrics = ["WallDuration", "CpuDuration_user", "CpuDuration_system"]

        # If the terms are missing, set as "N/A"
        curBucket = s.aggs.bucket(unique_terms[0], 'date_histogram', field=unique_terms[0], interval="day")
        new_unique_terms = unique_terms[1:]

        for term in new_unique_terms:
        	curBucket = curBucket.bucket(term, 'terms', field=term, missing="N/A")

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
            curTerm = unique_terms[index]

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
                            nowData[curTerm] = bucket[metric].value
                            # Add the doc count
                        nowData["Count"] = bucket['doc_count']
                        data.append(nowData)
                    else:
                        recurseBucket(nowData, bucket, index+1, data)


        	
        
        # We only want to hold onto 1 day's worth of summaries
        print len(response.aggregations['EndTime']['buckets'])
        for day in response.aggregations['EndTime']['buckets']:
            data = []
            recurseBucket({"EndTime": day['key_as_string']}, day, 1, data)
            yield data
    

        
        # Aggregate on njobs, WallDuration, CpuUserDuration, CpuSystemDuration
        # Or, unique keys on EndTime (day), VO, ProjectName, CommonName, DN, ResourceType, HostDescription, ApplicationExitCode, Grid, Cores
        
