#!/usr/bin/env python3

from appview import AppView
from controller.local_connection import LocalConnection
from controller.remote_connection import RemoteConnection
from multiprocessing import Process, Queue
from model.offer_lookup import OfferLookup
from model import run_server
import sys

ip="localhost"
port=8000

# parse arguments
if len(sys.argv) >=3:
    ip=sys.argv[2]
    if len(sys.argv) == 4:
        port=int(sys.argv[3])

if len(sys.argv) > 1:
    if sys.argv[1]=="serve":
        print(f"[application.py] launching server on {ip}:{port}")
        run_server(ip, port)
    
    elif sys.argv[1]=="client":
        print(f"[application.py] launching client to connect with {ip}:{port}")
        # configure for controller to use remote connection
        offerLookup=OfferLookup()
        appView=AppView()
        remoteConnection = RemoteConnection(appView.q_in, appView.q_out, ip, port)
        controller_process = Process(target=remoteConnection, daemon=True)
        controller_process.start()
        appView()

    else:
        print("invalid arguments", file=sys.stderr)
else:
    # configure for controller to use local connection
    offerLookup=OfferLookup()
    appView=AppView()

    localConnection = LocalConnection(appView.q_in, appView.q_out, offerLookup)
    controller_process = Process(target=localConnection, daemon=True)
    controller_process.start()

    appView()
