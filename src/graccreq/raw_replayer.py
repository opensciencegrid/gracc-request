import pika
import json
import sys
import logging
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import traceback
import replayer

def RawReplayerFactory(msg, parameters):
    # Create the raw replayer class
    #print "Creating raw replayer"
    try:
        replayer = RawReplayer(msg, parameters)
        replayer.run()
    except Exception, e:
        logging.error(traceback.format_exc())


class RawReplayer(replayer.Replayer):
    def __init__(self, message, parameters):
        super(RawReplayer, self).__init__(message, parameters)

        
    def run(self):
        logging.debug("Beggining run of RawReplayer")
        self.createConnection()

        
        # Send start message to control channel, if requested
        self.sendControlMessage({'status': 'ok', 'stage': 'starting'})

        # Query elsaticsearch and send the data to the destination
        logging.info("Sending response to %s with routing key %s" % (self.msg['destination'], self.msg['routing_key']))
        try:
            for record in self._queryElasticsearch(self.msg['from'], self.msg['to'], None):
                self.sendMessage(json.dumps(record.to_dict()))
        except Exception, e:
            logging.error("Exception caught in query ES: %s" % str(e))
            
        
        self.sendControlMessage({'status': 'ok', 'stage': 'finished'})
        
        self.conn.close()
        
        return
        
    def on_return(self, channel, method, properties, body):
        sys.stderr.write("Got returned message\n")
        
    def _queryElasticsearch(self, from_date, to_date, query):
        logging.debug("Connecting to ES")
        client = Elasticsearch()
        
        logging.debug("Beginning search")
        s = Search(using=client, index='gracc.osg.raw-*')
        s = s.filter('range', **{'@timestamp': {'from': from_date, 'to': to_date }})
        
        logging.debug("About to execute query:\n%s" % str(s.to_dict()))
        
        for hit in s.scan():
            yield hit
        

        
