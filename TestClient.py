# Based on lazy pirate pattern

import zmq
import sys
import numpy

def recv_array(socket, flags=0, copy=True, track=False):
    """recv a numpy array"""
    md = socket.recv_json(flags=flags)
    msg = socket.recv(flags=flags, copy=copy, track=track)
    buf = buffer(msg)
    A = numpy.frombuffer(buf, dtype=md['dtype'])
    return A.reshape(md['shape'])

REQUEST_TIMEOUT = 2500
REQUEST_RETRIES = 3
SERVER_ENDPOINT = "tcp://localhost:5555"

context = zmq.Context()

#  Socket to talk to server
print "Connecting to hello world server..."
client = context.socket(zmq.REQ)
client.connect(SERVER_ENDPOINT)

poll = zmq.Poller()
poll.register(client, zmq.POLLIN)

retries_left = REQUEST_RETRIES

while retries_left:
    shots_requested = 1
    request = str(shots_requested)  # ask for one shot of data
    print "I: Sending (%s)" % request

    client.send(request)

    expect_reply = True
    while expect_reply:
        socks = dict(poll.poll(REQUEST_TIMEOUT))
        if socks.get(client) == zmq.POLLIN:
            reply = client.recv()
            if not reply:
                break
            if int(reply) == shots_requested:
                print "I: Server replied OK (%s)" % reply
                retries_left = REQUEST_RETRIES
                expect_reply = False
            else:
                print "E: Malformed reply from server: %s" % reply

        else:
            print "W: No response from server, retrying..."
            # Socket is confused. Close and remove it.
            client.setsockopt(zmq.LINGER, 0)
            client.close()
            poll.unregister(client)
            retries_left -= 1
            if retries_left == 0:
                print "E: Server seems to be offline, abandoning"
                break
            print "I: Reconnecting and resending (%s)" % request
            # Create new connection
            client = context.socket(zmq.REQ)
            client.connect(SERVER_ENDPOINT)
            poll.register(client, zmq.POLLIN)
            client.send(request)

context.term()
