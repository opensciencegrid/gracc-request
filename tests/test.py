import json
import pika
import sys



credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost',
                                        5672, '/', credentials)
conn = pika.adapters.blocking_connection.BlockingConnection(parameters)

channel = conn.channel()


msg = """
{
  "time_range": "now-3d",
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

msg_json = json.loads(msg)

# Create the receive queue
channel.queue_declare(queue='test_queue', durable=False, exclusive=True, auto_delete=True)
channel.exchange_declare(exchange='test_exchange', exchange_type='direct', durable=False, auto_delete=True)
channel.queue_bind(queue='test_queue', exchange='test_exchange', routing_key='test_key')

# Set the destination
msg_json['destination'] = 'test_exchange'
msg_json['routing_key'] = 'test_key'

def getMessage(channel, method, properties, body):
    print "Got Body:"
    print body
    channel.stop_consuming()

channel.basic_consume(getMessage, "test_queue")

channel.basic_publish('gracc.osg.requests',
                      'gracc.osg.requests',
                      json.dumps(msg_json),
                      pika.BasicProperties(content_type='text/json',
                                           delivery_mode=1))
                                           


def deadline_reached():
    print "Deadline reached"
    channel.stop_consuming()
    sys.exit(1)
    
conn.add_timeout(10, deadline_reached)                                           


channel.start_consuming()



print "Exiting after basic_get"
conn.close()
