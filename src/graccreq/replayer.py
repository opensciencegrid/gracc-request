import logging
import pika
import json



class Replayer(object):
    """
    Base for all replayers.  It provides functions for sending messages to the control
    channel, creating and sending data to the destination.
    """
    def __init__(self, message, parameters):
        self.msg = message
        self.parameters = parameters
        self.control = False
        if 'control' in self.msg and self.msg['control']:
            self.control = True
            self.control_exchange = self.msg['control']
            self.control_key = self.msg['control_key']
        
        self.conn = None
            
    def createConnection(self):
        """
        Create the connection to the rabbitmq server.
        
        """
        if not self.conn:
            self.conn = pika.adapters.blocking_connection.BlockingConnection(self.parameters)
            self.chan = self.conn.channel()
            self.chan.add_on_return_callback(self.on_return)
            
    def sendMessage(self, msg):
        """
        Send message (or data) to the destination in the query message.
        
        :param str msg: Stringified message to send to remote receiver.  Should be json.
        
        """
        if not self.conn:
            self.createConnection()
        try:
            self.chan.basic_publish(self.msg['destination'], self.msg['routing_key'], msg,
                                 pika.BasicProperties(content_type='text/json',
                                 delivery_mode=1))
        except Exception as e:
            logging.error("Exception caught in basic_publish: %s" % str(e))
            raise e
            
            
    def sendControlMessage(self, control_msg):
        """
        Send a contorl message to the control exchange defined in the query
        message.
        
        :param dict control_msg: Dict message to send to control exchange.
        
        """
        if not self.control:
            return
            
        if not self.conn:
            self.createConnection()
        
        try:
            logging.debug("Sending command to control exchange %s" % self.control_exchange)
            self.chan.basic_publish(self.control_exchange, self.control_key, json.dumps(control_msg),
                                 pika.BasicProperties(content_type='text/json',
                                           delivery_mode=1))
        except Exception as e:
            logging.error("Exception caught in sending start msg to control channel %s: %s" % (self.control_exchange, str(e)))