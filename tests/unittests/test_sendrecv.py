import json
import pika
import sys
import unittest
from datetime import datetime, timedelta
import string
import random


class TestSendRecv(unittest.TestCase):
    
    def _createName(self, size=6):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))
    
    def setUp(self):
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters('localhost',
                                                5672, '/', credentials)
        self.conn = pika.adapters.blocking_connection.BlockingConnection(parameters)

        self.channel = self.conn.channel()


        self.msg = """
        {
          "kind": "raw",
          "filter": {
            "query": {
              "query_string": {
                "query": "vo=cms"
              }
            }
          }
        }
        """
        # Create the receive queue
        self.channel.queue_declare(queue='test_queue', durable=False, exclusive=True, auto_delete=True)
        self.channel.exchange_declare(exchange='test_exchange', exchange_type='direct', durable=False, auto_delete=True)
        self.channel.queue_bind(queue='test_queue', exchange='test_exchange', routing_key='test_key')
        
        # Create the control queue
        self.control_queue = "control-queue-%s" % self._createName()
        control_exchange = "control-exchange-%s" % self._createName()
        routing_key = "control-key-%s" % self._createName()
        self.channel.queue_declare(queue=self.control_queue, durable=False, exclusive=True, auto_delete=True)
        self.channel.exchange_declare(control_exchange, exchange_type='direct', durable=False, auto_delete=True)
        self.channel.queue_bind(queue=self.control_queue, exchange=control_exchange, routing_key=routing_key)
        
        self.msg_json = json.loads(self.msg)
        # Set the destination
        self.msg_json['destination'] = 'test_exchange'
        self.msg_json['routing_key'] = 'test_key'
        self.msg_json['control'] = control_exchange
        self.msg_json['control-key'] = routing_key
        
        # Set the timerange
        start_time = datetime(2016, 5, 10)
        
        self.msg_json['from'] = str(start_time.isoformat())
        self.msg_json['to'] = str((start_time + timedelta(days=1)).isoformat())
    
    def test_sendrecv(self):
        status = {'body': "", 'control': "", 'num_messages': 0}
        def getMessage(channel, method, properties, body):
            status['body'] = body
            status['num_messages'] += 1
            self.channel.basic_ack(delivery_tag=method.delivery_tag)
            
        def getControlMessage(channel, method, properties, body):
            status['control'] = body
            self.channel.basic_ack(delivery_tag=method.delivery_tag)
            

        def deadline_reached():
            #print "Deadline reached"
            self.channel.stop_consuming()


        self.channel.basic_consume(getMessage, "test_queue")
        self.channel.basic_consume(getControlMessage, self.control_queue)

        
        self.channel.basic_publish('gracc.osg.requests',
                              'gracc.osg.requests',
                              json.dumps(self.msg_json),
                              pika.BasicProperties(content_type='text/json',
                                                   delivery_mode=1))
        

                                                   
        self.conn.add_timeout(10, deadline_reached)   
        
        self.channel.start_consuming()

        self.assertGreater(len(status['body']), 0)
        self.assertGreater(len(status['control']), 0)
        self.assertEqual(status['num_messages'], 10)
        
        self.conn.close()



                                           



    
                                        







