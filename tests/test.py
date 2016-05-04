import json
import pika



credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost',
                                        5672, '/', credentials)
conn = pika.adapters.blocking_connection.BlockingConnection(parameters)

channel = conn.channel()


msg = """
{
 "time_range": "now-3d",
 "kind": "raw",
 "destination": "/grace.osg.raw",
 "filter": {
            "query": {
             "query_string": {
              "query": "vo=cms"
             }
            }
           }
}
"""


channel.basic_publish('gracc.osg.requests',
                      'gracc.osg.requests',
                      msg,
                      pika.BasicProperties(content_type='text/json',
                                           delivery_mode=1))

conn.close()
