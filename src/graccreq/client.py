import json
import pika
import sys
from datetime import datetime, timedelta
import string
import random



class Client:
    """
    Client application to the GRACC Request daemons
    """
    
    def __init__(self, exchange, routing_key, url="amqp://guest:guest@localhost/"):
        """
        Initialization function
            
        :param str exchange: Exchange to send requests to.
        :param str routing_key: Routing key to bind to.
        :param str url: URL of the amqp connection.  Can be in the form of scheme://username:password@host:port/vhost
        """
        
        self.url = url
        self.exchange = exchange
        self.routing_key = routing_key
        
        self.conn = None
        self.messages_received = 0
        self.last_messages = 0
        
        
    def _createQueues(self, create_data):
        """
        Create the necessary queues and exchanges for data and control messages to be received.
        
        :param boolean create_data: Whether to create the data exchanges or not.  Setting to true will create the data channels.
        """
        if not self.conn:
            self._createConn()
            
        # Create a new channel
        self.channel = self.conn.channel()
        
        if create_data:
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
        """
        Create a unique string name.
        """
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))
    
    def _createConn(self):
        """
        Initiate the remote connection
        """
        parameters = pika.URLParameters(self.url)
        self.conn = pika.adapters.blocking_connection.BlockingConnection(parameters)
        
    def _getControlMessage(self, channel, method, properties, body):
        """
        Receives control messages from the remote agents
        """
        # Receives the control messages
        body_parsed = json.loads(body)
        self.channel.basic_ack(delivery_tag=method.delivery_tag)
        if body_parsed['stage'] == "finished":
            def deadline_reached():
                #print "Deadline reached"
                self.channel.stop_consuming()
            self.conn.add_timeout(1, deadline_reached)
        
    def _getDataMessage(self, channel, method, properties, body):
        """
        Receives the data messages
        """
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
            self.timer_id = self.conn.add_timeout(300, self._checkStatus)   
            
        
        
    def query(self, from_date, to_date, kind, getMessage=None, destination_exchange=None, destination_key=None):
        """
        Query the remote agents for data.
        
        :param datetime from_date: A python datetime object representing the begininng of the query's time interval.
        :param datetime to_date: A python datetime object representing the end of the query's time interval
        :param str kind: The kind of request.  Either "raw", "summary", or "transfer_summary"
        :param function getMessage: A callback to send the received records.
        :param str destination_exchange: The name of the exchange to send data to.
        :param str destination_key: The routing key to use for destination.
        
        Either getMessage is None, or both destination_exchange and destination_key are None.  getMessage is used
        to retrieve data inline, while destination_exchange and destination_key are used to route traffic elsewhere.
        
        destination_exchange has to already exist.
        """
        
        # Check that we don't have conflicting variable states
        assert (getMessage == None) or ((destination_exchange == None) and (destination_key == None))
        
        # Convinence variable to see if we are receiving the data, or not
        remote_destination = (destination_exchange != None) and (destination_key != None)
        
        # Create the connection
        self._createConn()
        self._createQueues(not remote_destination)
        
        # First, create the msg
        msg = {}
        msg["from"] = from_date.isoformat()
        msg["to"] = to_date.isoformat()
        msg["kind"] = kind
        if remote_destination:
            msg["destination"] = destination_exchange
            msg["routing_key"] = destination_key
        else:
            msg["destination"] = self.data_exchange
            msg["routing_key"] = self.data_key
        msg["control"] = self.control_exchange
        msg["control_key"] = self.control_key
        
        # Now listen to the queues
        self.callbackDataMessage = getMessage
        self.channel.basic_consume(queue=self.control_queue, on_message_callback=self._getControlMessage)
        if not remote_destination:
            self.channel.basic_consume(queue=self.data_queue, on_message_callback=self._getDataMessage)

        # Send the message
        self.channel.basic_publish(self.exchange,
                              self.routing_key,
                              json.dumps(msg),
                              pika.BasicProperties(content_type='text/json',
                                                   delivery_mode=1))
        

        # Begin the checkStatus timer
        self.timer_id = self.conn.add_timeout(300, self._checkStatus)   
        
        self.channel.start_consuming()
        
        self.conn.close()
        self.conn = None
        
        

