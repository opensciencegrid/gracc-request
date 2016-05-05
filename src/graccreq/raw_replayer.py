import pika
import json
import sys
import logging

def RawReplayerFactory(msg, parameters):
    # Create the raw replayer class
    #print "Creating raw replayer"
    replayer = RawReplayer(msg, parameters)
    replayer.run()


class RawReplayer:
    def __init__(self, message, parameters):
        self.msg = message
        self.parameters = parameters
        
    def run(self):
        logging.debug("Beggining run of RawReplayer")
        #print "Running raw replayer"
        
        # Query elsaticsearch
        
        # Return the results
        toReturn = {}
        toReturn['status'] = 'ok'
        self._conn = pika.adapters.blocking_connection.BlockingConnection(self.parameters)
        self._chan = self._conn.channel()
        self._chan.add_on_return_callback(self.on_return)
        logging.info("Sending response to %s with routing key %s" % (self.msg['destination'], self.msg['routing_key']))
        try:
            self._chan.basic_publish(self.msg['destination'], self.msg['routing_key'], json.dumps(toReturn),
                                 pika.BasicProperties(content_type='text/json',
                                           delivery_mode=1))
        except Exception, e:
            logging.error("Exception caught in basic_publish: %s" % str(e))
            
        self._conn.close()
        
        return
        
    def on_return(channel, method, properties, body):
        sys.stderr.write("Got returned message\n")
        
        
