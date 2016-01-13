# Camera server, initializes camera, and wait for requests for data shots.
# Based on lazy-pirate pattern

import zmq
import time
import numpy
import sys

sys.path.append("/home/photon/code/PythonForPicam")

print("Initializing PICAM library...")
from pypicam import *
ccdcam = PyPICAM()
ccdcam.configure_camera(roi=[340,210,600,10,1,1])
ccdcam.get_temp()


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

while True:
    try:
        message = server.recv()
        print("Received request: ", message)

        # collect message number of shots
        shots = int(message)
        if shots > 0 and shots <= 100:
            ccdcam.acquire(N=shots)

            # Send reply
            data = ccdcam.get_all_data()

            #server.send(message)  # this will be the data message
            send_array(server, data)
        else:
            print("W: Request out of range (0 < N <= 100)")
    except KeyboardInterrupt:
        print("W: interrupt received, ending service")
        break

server.close()
context.term()
ccdcam.close()
print("W: server closed, and PICAM unloaded.")
