#!/usr/bin/env python3

from http.server import *
from model.offer_lookup import OfferLookup
import json
import asyncio
from multiprocessing import Process, Queue
from multiprocessing.queues import Empty
import time
import decimal
from dataclasses import dataclass
import sys
import debug

# offerLookup = OfferLookup()


class HTTPRequestHandler(BaseHTTPRequestHandler):
    """process incoming signals in the form of { id:, msg: { subnet:, sql: } } by relaying via q_out_to_model"""

    # https://stackoverflow.com/questions/1960516/python-json-serialize-a-decimal-object

    def do_GET(self):
        class DecimalEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, decimal.Decimal):
                    return str(o)
                return super(DecimalEncoder, self).default(o)

        content_len = int(self.headers.get("Content-Length"))
        b = self.rfile.read(content_len)
        msg = json.loads(b.decode("utf-8"))
        self.server.q_out_to_controller.put_nowait(
            msg
        )  # relay the received content to async_run_server

        signal = None
        while not signal:
            try:
                signal = (
                    self.server.q_in_from_controller.get_nowait()
                )  # offer lookup's dictionary came back
            except Empty:
                signal = None
            if signal:
                # relay signal as response
                results_json = json.dumps(signal, cls=DecimalEncoder)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(results_json.encode(encoding="utf-8"))

            time.sleep(0.01)


class MyHTTPServer(HTTPServer):
    q_in_from_controller = None
    q_out_to_controller = None


def _run_server(
    ip,
    port,
    q_in_from_controller,
    q_out_to_controller,
    server_class=MyHTTPServer,
    handler_class=HTTPRequestHandler,
):
    server_address = (ip, port)
    httpd = server_class(server_address, handler_class)
    httpd.q_in_from_controller = q_in_from_controller
    httpd.q_out_to_controller = q_out_to_controller
    httpd.serve_forever()


async def async_run_server(ip, port):
    offerLookup = OfferLookup()
    # identify the queues for message passing with HTTPRequestHandler
    q_out_to_httpbase = Queue()
    q_in_from_httpbase = Queue()

    server_process = Process(
        target=_run_server,
        args=(ip, port, q_out_to_httpbase, q_in_from_httpbase),
        daemon=True,
    )
    server_process.start()

    while True:
        try:
            signal = (
                q_in_from_httpbase.get_nowait()
            )  # get http body json over the remote wire via the synchronous HTTPRequestHandler
        except Empty:
            signal = None
        if signal:  # interact with yagna to lookup the offer
            results_l = await offerLookup(
                signal["id"], signal["msg"]["subnet-tag"], signal["msg"]["sql"], manual_probe=True, appkey=signal["msg"]["appkey"]
            )
            if results_l and len(results_l) > 0:
                if results_l[0] == "error" and results_l[1] == 401:
                    msg = ["error", "invalid api key server side"]
                    msg_out = {"id": signal["id"], "msg": msg}
                    q_out_to_httpbase.put_nowait(msg_out)
                elif results_l[0] == "error" and results_l[1] == 111:
                    msg = ["error", "cannot connect to yagna"]
                    msg_out = {"id": signal["id"], "msg": msg}
                    q_out_to_httpbase.put_nowait(msg_out)
                else:
                    msg_out = {"id": signal["id"], "msg": results_l}
                    q_out_to_httpbase.put_nowait(msg_out)
            else:
                print("[async_run_server]::ERROR", file=sys.stderr)
        await asyncio.sleep(0.01)


def run_server(ip, port):
    if ip == "localhost":
        ip = ""
    asyncio.run(async_run_server(ip, port))


if __name__ == "main":
    # asyncio.run(async_run_server)
    run_server(ip="localhost", port=8000)
