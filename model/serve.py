#!/usr/bin/env python3

from http.server import *
from model.offer_lookup import OfferLookup
import json
import asyncio
from multiprocessing import Process, Queue
from multiprocessing.queues import Empty
import time
import decimal

offerLookup=OfferLookup()

global_server_q_in = Queue()
global_server_q_out = Queue()

# https://stackoverflow.com/questions/1960516/python-json-serialize-a-decimal-object
class DecimalEncoder(json.JSONEncoder):
   def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        content_len = int(self.headers.get('Content-Length'))
        b=self.rfile.read(content_len)
        msg=json.loads(b.decode("utf-8"))
        global_server_q_out.put_nowait(msg) # offer lookup on main thread

        signal=None
        while not signal:
            try:
                signal = global_server_q_in.get_nowait() # offer lookup's dictionary came back
            except Empty:
                signal = None
            if signal:
                # relay signal as response
                results_json = json.dumps(signal, cls=DecimalEncoder)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(results_json.encode(encoding='utf-8'))

            time.sleep(0.01)





def _run_server(ip, port, server_class=HTTPServer, handler_class=HTTPRequestHandler):
    server_address=(ip, port)

    httpd=server_class(server_address, handler_class)
    httpd.serve_forever()







async def async_run_server(ip, port):
    offerLookup=OfferLookup()
    q_out=global_server_q_in
    q_in=global_server_q_out
    server_process=Process(target=_run_server, args=(ip, port), daemon=True)
    server_process.start()

    while True:
        try:
            signal = q_in.get_nowait() # get the id and sql over the remote wire
        except Empty:
            signal = None
        if signal: # interact with yagna to lookup the offer
            results_d = await offerLookup(signal["id"], signal["sql"])

            if results_d:
                msg_out = { "id": signal["id"], "msg": results_d }
                q_out.put_nowait(msg_out)
            else:
                print("[async_run_server]::ERROR")
        await asyncio.sleep(0.01) 


def run_server(ip, port):
    asyncio.run(async_run_server(ip, port))


if __name__ == "main":
    # asyncio.run(async_run_server)
    run_server(ip="localhost", port=8000)

