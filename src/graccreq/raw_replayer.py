import pika


def RawReplayerFactory(msg):
    # Create the raw replayer class
    print "Creating raw replayer"
    replayer = RawReplayer(msg)
    replayer.run()


class RawReplayer:
    def __init__(self, message):
        self.msg = message
        
    def run(self):
        print "Running raw replayer"
        
        # Query elsaticsearch
        
        # Return the results
        msg = "blah"
        
        
        
        
