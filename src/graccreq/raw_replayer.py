import pika
import json


def RawReplayerFactory(msg, channel):
    # Create the raw replayer class
    #print "Creating raw replayer"
    replayer = RawReplayer(msg, channel)
    replayer.run()


class RawReplayer:
    def __init__(self, message, channel):
        self.msg = message
        self.channel = channel
        
    def run(self):
        #print "Running raw replayer"
        
        # Query elsaticsearch
        
        # Return the results
        toReturn = {}
        toReturn['status'] = 'ok'
        self.channel.basic_publish(self.msg['desitnation'], self.msg['routing_key'], json.dumps(toReturn))
        
        return
        
        
        
        
