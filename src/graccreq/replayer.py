import logging
import pika
import json



class Replayer(object):
    def __init__(self, message, parameters):
        self.msg = message
        self.parameters = parameters
        self.control = False
        if 'control' in self.msg and self.msg['control']:
            self.control = True
            self.control_exchange = self.msg['control']
            self.control_key = self.msg['control-key']
        
        self.conn = None
            
    def createConnection(self):
        if not self.conn:
            self.conn = pika.adapters.blocking_connection.BlockingConnection(self.parameters)
            self.chan = self.conn.channel()
            self.chan.add_on_return_callback(self.on_return)
            
            
    def sendControlMessage(self, control_msg):
        
        if not self.control:
            return
            
        if not self.conn:
            self.createConnection()
        
        try:
            logging.debug("Sending command to control exchange %s" % self.control_exchange)
            self.chan.basic_publish(self.control_exchange, self.control_key, json.dumps(control_msg),
                                 pika.BasicProperties(content_type='text/json',
                                           delivery_mode=1))
        except Exception, e:
            logging.error("Exception caught in sending start msg to control channel %s: %s" % (self.control_exchange, str(e)))