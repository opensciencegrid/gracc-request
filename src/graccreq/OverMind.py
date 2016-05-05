
from multiprocessing import Pool, TimeoutError
import json
import pika
import sys
from raw_replayer import RawReplayerFactory
import toml
import argparse


class OverMind:
    """
    Top level class that listens to for requests
    """
    
    def __init__(self, configuration):
        
        self._pool = None
        
        # Import the configuration
        self._config = {}
        with open(configuration, 'r') as config_file:
            self._config = toml.loads(config_file.read())

    
    def run(self):
        """
        Event Loop
        """
        
        # Start up the pool processes
        self._pool = Pool(processes=4)
        self.createConnection()
        self._chan.basic_consume(self._receiveMsg, 'gracc.osg.requests')
        
        # The library gives us an event loop built-in, so lets use it!
        # This program only responds to messages on the rabbitmq, so no
        # reason to listen to anything else.
        try:
            self._chan.start_consuming()
        except KeyboardInterrupt:
            self._chan.stop_consuming()
        
        sys.exit(1)
        
        

    def createConnection(self):
        credentials = pika.PlainCredentials(self._config['AMQP']['username'], self._config['AMQP']['password'])
        parameters = pika.ConnectionParameters(self._config['AMQP']['host'],
                                                5672, self._config['AMQP']['vhost'], credentials)
        self._conn = pika.adapters.blocking_connection.BlockingConnection(parameters)
        
        self._chan = self._conn.channel()
        # Create the exchange, if it doesn't already exist
        # TODO: capture exit codes on all these call
        self._chan.exchange_declare(exchange='gracc.osg.requests', exchange_type='direct')
        self._chan.queue_declare(queue='gracc.osg.requests')
        self._chan.queue_bind('gracc.osg.requests', 'gracc.osg.requests')
        #self._chan.queue_declare(queue="request_raw", durable=True, auto_delete=False, exclusive=False)
        
        
    def _receiveMsg(self, channel, method_frame, header_frame, body):
        print method_frame.delivery_tag
        print body
        msg_body = {}
        
        try:
            msg_body = json.loads(body)
        except ValueError, e:
            print "Unable to json parse the body of the message"
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            return
        
        #print msg_body
        # TODO: some sort of whitelist, authentication?
        if msg_body['kind'] == 'raw':
            #print "Starting raw replayer"
            
            self._pool.apply_async(RawReplayerFactory, (msg_body, channel))
        elif msg_body['kind'] == 'summary':
            #print "Starting summary replayer"
        
        #print
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="GRACC Request Daemon")
    parser.add_argument("-c", "--configuration", help="Configuration file location",
                        default="/etc/graccreq/config.toml", dest='config')
    args = parser.parse_args()
    
    
    # Create and run the OverMind
    overmind = OverMind(args.config)
    overmind.run()
    
    


