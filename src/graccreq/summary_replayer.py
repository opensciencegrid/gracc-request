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
from graccreq.oim import projects, OIMTopology, voinfo, nsfscience
import StringIO
from graccreq.correct import Corrections


def SummaryReplayerFactory(msg, parameters, config):
    
    # Start profiling
    if 'General' in config and 'Profile' in config['General'] and config['General']['Profile']:
        logging.debug("Staring profiler")
        import cProfile
        pr = cProfile.Profile()
        pr.enable()
        
    try:
        replayer = SummaryReplayer(msg, parameters, config)
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
        
        
class SummaryReplayer(replayer.Replayer):
    def __init__(self, message, parameters, config):
        super(SummaryReplayer, self).__init__(message, parameters)
        self._config = config
        
        # Initialize the project information
        self.project = projects.OIMProjects(url=self._config['OIM_URLs'].get('projects'))

        # Initialize the OIM Topology information
        self.topology = OIMTopology.OIMTopology(url=self._config['OIM_URLs'].get('oimtopology'))

        # Initialize the OIM VO information
        self.oimvoinfo = voinfo.OIMVOInfo(url=self._config['OIM_URLs'].get('voinfo'))

        # Intialize the OIM NSF Information
        self.nsfscience = nsfscience.NSFScience(url=self._config['OIM_URLs'].get('nsfscience'))

        # Initiatlize name corrections
        self.corrections = []
        for c in self._config.get('Corrections',[]):
            self.corrections.append(Corrections(uri=self._config['ElasticSearch'].get('uri','http://localhost:9200'),
                                                index=c['index'],
                                                doc_type=c['doc_type'],
                                                match_fields=c['match_fields'],
                                                source_field=c['source_field'],
                                                dest_field=c['dest_field'],
                                                regex=c.get('regex', False),
                                                force_overwrite=c.get('force_overwrite', False)))
        
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
                    for c in self.corrections:
                        c.correct(record)
                    self.addProperties(record)
                    self.sendMessage(json.dumps(record))
        except Exception, e:
            logging.error("Exception caught in query ES: %s" % str(e))
            logging.error(traceback.format_exc())
            raise e
            
        
        self.sendControlMessage({'status': 'ok', 'stage': 'finished'})
        
        self.conn.close()
        


    def on_return(self, channel, method, properties, body):
        sys.stderr.write("Got returned message\n")

    def addProperties(self, record):
        
        # If ProjectName is "N/A", then set 
        # ProjectName to VOName
        if ('VOName' in record and 
            (('ProjectName' not in record) or
            ('ProjectName' in record and record["ProjectName"].lower() == "n/a") or
            ('ProjectName' in record and record["ProjectName"].lower() == "unknown"))):
            record["ProjectName"] = record["VOName"]
            
        returned_doc = self.project.parseDoc(record)
        topology_doc = self.topology.generate_dict_for_gracc(record)
        vo_doc = self.oimvoinfo.parse_doc(record)
        record.update(returned_doc)
        record.update(topology_doc)
        record.update(vo_doc)

        nsf_doc = self.nsfscience.parseDoc(record)
        record.update(nsf_doc)
        
        # If OIM_Site (which is used as display name) is not in the record,
        # set it to Host_description, if that's in the record
        if 'OIM_Site' not in record and 'Host_description' in record:
            record['OIM_Site'] = record['Host_description']
        
        return record
        
    def _queryElasticsearch(self, from_date, to_date, query):
        logging.debug("Connecting to ES")
        client = Elasticsearch(timeout=300)
        
        # For summaries, we only summarize full days, so strip the time from the from & to
        # Round the date up, so we get the entire last day they requested.
        from_date = dateutil.parser.parse(from_date).date()
        to_date = dateutil.parser.parse(to_date).date() + datetime.timedelta(days=1)
        
        logging.debug("Beginning search")
        s = Search(using=client, index=self._config['ElasticSearch']['raw_index'])
        s = s.filter('range', **{'EndTime': {'from': from_date, 'to': to_date }})
        s = s.query('bool', must=[Q('match', _type=self._config['ElasticSearch']['raw_type'])])
        
        # Fill in the unique terms and metrics
        unique_terms = [["EndTime", 0], ["VOName", "N/A"], ["ProjectName", "N/A"], ["DN", "N/A"], ["Processors", 1], ["GPUs", 0], ["ResourceType", "N/A"], ["CommonName", "N/A"], ["Host_description", "N/A"], ["Resource_ExitCode", 0], ["Grid", "N/A"], ["ReportableVOName", "N/A"], ["ProbeName", "N/A"], ["SiteName", "N/A"]]
        metrics = [["WallDuration", 0], ["CpuDuration_user", 0], ["CpuDuration_system", 0], ["CoreHours", 0], ["Njobs", 1], ["CpuDuration", 0]]

        # If the terms are missing, set as "N/A"
        curBucket = s.aggs.bucket(unique_terms[0][0], 'date_histogram', field=unique_terms[0][0], interval="day")
        new_unique_terms = unique_terms[1:]

        for term in new_unique_terms:
        	curBucket = curBucket.bucket(term[0], 'terms', field=term[0], missing=term[1], size=(2**31)-1)

        for metric in metrics:
        	curBucket.metric(metric[0], 'sum', field=metric[0], missing=metric[1])
            
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
                            nowData[metric[0]] = bucket[metric[0]].value
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
        
