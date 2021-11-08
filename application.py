#!/usr/bin/env python3

from appview import AppView
from controller.local_connection import LocalConnection
from multiprocessing import Process, Queue
from model.offer_lookup import OfferLookup
from model import run_server
import sys

if len(sys.argv) > 1 and sys.argv[1]=="serve":
    run_server()
else:
    offerLookup=OfferLookup()
    appView=AppView()

    localConnection = LocalConnection(appView.q_in, appView.q_out, offerLookup)
    controller_process = Process(target=localConnection, daemon=True)
    controller_process.start()

    appView()
