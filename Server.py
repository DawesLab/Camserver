# Camera server, initializes camera, and wait for requests for data shots.
# Based on lazy-pirate pattern

import zmq
import time
import numpy
import sys

sys.path.append("/home/photon/code/PythonForPicam")

print "Initializing PICAM library..."
from pypicam import *
ccdcam = PyPICAM()
ccdcam.configure_camera()


def send_array(socket, A, flags=0, copy=False, track=False):
    """send a numpy array with metadata"""
    md = dict(
        dtype=str(A.dtype),
        shape=A.shape,
    )
    socket.send_json(md, flags | zmq.SNDMORE)
    return socket.send(A, flags, copy=copy, track=track)

context = zmq.Context()

server = context.socket(zmq.REP)

server.bind("tcp://*:5555")

test_array = numpy.array([1, 2, 3, 4])
while True:
    try:
        message = server.recv()
        print "Received request: ", message

        # collect message number of shots (TODO verify message is int)
        ccdcam.acquire(N=int(message))

        # Send reply
        data = ccdcam.get_data()

        #server.send(message)  # this will be the data message
        send_array(server, data)
    except KeyboardInterrupt:
        print "W: interrupt received, ending service"
        break

server.close()
context.term()
Picam_UninitializeLibrary()
print "W: server closed, and PICAM unloaded."
