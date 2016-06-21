import json
import pika
import sys
from datetime import datetime, timedelta
import string
import random



class Client:
    
    def __init__(self, exchange, host="localhost", username="guest", password="guest"):
        
        self.host = host
        self.username = username
        self.password = password
        self.exchange = exchange
        
        self.conn = None
        self.messages_received = 0
        self.last_messages = 0
        
        
    def _createQueues(self):
        if not self.conn:
            self._createConn()
            
        # Create a new channel
        self.channel = self.conn.channel()
        
        # Create the receive queue
        self.data_queue = "data-queue-%s" % self._createName()
        self.data_exchange = "data-exchange-%s" % self._createName()
        self.data_key = "data-key-%s" % self._createName()
        self.channel.queue_declare(queue=self.data_queue, durable=False, exclusive=True, auto_delete=True)
        self.channel.exchange_declare(exchange=self.data_exchange, exchange_type='direct', durable=False, auto_delete=True)
        self.channel.queue_bind(queue=self.data_queue, exchange=self.data_exchange, routing_key=self.data_key)
        
        # Create the control queue
        self.control_queue = "control-queue-%s" % self._createName()
        self.control_exchange = "control-exchange-%s" % self._createName()
        self.control_key = "control-key-%s" % self._createName()
        self.channel.queue_declare(queue=self.control_queue, durable=False, exclusive=True, auto_delete=True)
        self.channel.exchange_declare(exchange=self.control_exchange, exchange_type='direct', durable=False, auto_delete=True)
        self.channel.queue_bind(queue=self.control_queue, exchange=self.control_exchange, routing_key=self.control_key)
        
        
        
    def _createName(self, size=6):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))
    
    def _createConn(self):
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(self.host,
                                                5672, '/', credentials)
        self.conn = pika.adapters.blocking_connection.BlockingConnection(parameters)
        
    def _getControlMessage(self, channel, method, properties, body):
        # Receives the control messages
        body_parsed = json.loads(body)
        self.channel.basic_ack(delivery_tag=method.delivery_tag)
        if body_parsed['stage'] == "finished":
            def deadline_reached():
                #print "Deadline reached"
                self.channel.stop_consuming()
            self.conn.add_timeout(1, deadline_reached)
        
    def _getDataMessage(self, channel, method, properties, body):
        self.channel.basic_ack(delivery_tag=method.delivery_tag)
        self.messages_received += 1
        self.callbackDataMessage(body)
        
    def _checkStatus(self):
        """
        Called every X seconds to check the status of the transfer.
        If nothing has happened lately, then kill the connection.
        """
        
        if self.last_messages == self.messages_received:
            self.channel.stop_consuming()
        else:
            self.last_messages = self.messages_received
            self.timer_id = self.conn.add_timeout(10, self._checkStatus)   
            
        
        
    def query(self, from_date, to_date, kind, getMessage):
        
        # Create the connection
        self._createConn()
        self._createQueues()
        
        # First, create the msg
        msg = {}
        msg["from"] = from_date.isoformat()
        msg["to"] = to_date.isoformat()
        msg["kind"] = kind
        msg["destination"] = self.data_exchange
        msg["routing_key"] = self.data_key
        msg["control"] = self.control_exchange
        msg["control_key"] = self.control_key
        
        # Now listen to the queues
        self.callbackDataMessage = getMessage
        self.channel.basic_consume(self._getDataMessage, self.data_queue)
        self.channel.basic_consume(self._getControlMessage, self.control_queue)

        # Send the message
        self.channel.basic_publish(self.exchange,
                              'gracc.osg.requests',
                              json.dumps(msg),
                              pika.BasicProperties(content_type='text/json',
                                                   delivery_mode=1))
        
        # If we don't get any messages for 10 seconds, then stop the client                                       
        def deadline_reached():
            if self.messages_received == 0:
                self.channel.stop_consuming()
                                                   
        self.timer_id = self.conn.add_timeout(10, self._checkStatus)   
        
        self.channel.start_consuming()
        
        self.conn.close()
        self.conn = None
        
        

