#!/usr/bin/env python3

from appview import AppView
from controller.local_connection import LocalConnection
from controller.remote_connection import RemoteConnection
from multiprocessing import Process, Queue, freeze_support
import sys

if __name__ == "__main__":
    ip="localhost"
    port=8000

    # parse arguments
    if len(sys.argv) >=3:
        ip=sys.argv[2]
        if len(sys.argv) == 4:
            port=int(sys.argv[3])

    if len(sys.argv) > 1:
        if sys.argv[1]=="serve":
            from model import run_server
            from model.offer_lookup import OfferLookup
            from controller.remote_connection import RemoteConnection
            print(f"[application.py] launching server on {ip}:{port}")
            run_server(ip, port)
        
        elif sys.argv[1]=="client":
            from controller.local_connection import LocalConnection
            print(f"[application.py] launching client to connect with {ip}:{port}")
            # configure for controller to use remote connection
            # offerLookup=OfferLookup(SERVER)
            appView=AppView()
            remoteConnection = RemoteConnection(appView.q_in, appView.q_out, ip, port)
            controller_process = Process(target=remoteConnection, daemon=True)
            # freeze_support()
            controller_process.start()
            appView()

        else:
            print("invalid arguments", file=sys.stderr)
    else:
        # configure for controller to use local connection
        from model.offer_lookup import OfferLookup
        offerLookup=OfferLookup()
        appView=AppView()

        localConnection = LocalConnection(appView.q_in, appView.q_out, offerLookup)
        controller_process = Process(target=localConnection, daemon=True)
        # freeze_support()
        controller_process.start()

        appView()
