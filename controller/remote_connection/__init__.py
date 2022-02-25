# remote_connection/__init__.py
from multiprocessing.queues import Empty
import asyncio
import json
import debug
import sys

"""
messages come in from the view on a queue as in LocalConnection
the message queue is continually monitored to handle them, thus like LocalConnection, this is run in a process
since asynchronous constructs are incompatible with the gui (non-async only)

as in LocalConnection, the keys of interest from the view are "id" and "msg" where msg contains the sql
in LocalConnection, the callback is given the id and sql and this callback is OfferLookup() from the model
but this is now run remotely
so a proxy is needed (http) so that OfferLookup runs remotely
the http client shall be implemented here
it shall attempt to connect then send the request and get the server's response as a json
"""

import http.client


class RemoteConnection:
    """functor that sets up full duplex queues to the view and monitors for then relays requests to remote model"""

    def __init__(self, q_out, q_in, addr, port):
        self.q_out = q_out
        self.q_in = q_in
        self.addr = addr
        self.port = port

    async def poll_loop(self):
        results_d = None
        signal = None
        while True:
            try:
                signal = self.q_in.get_nowait()
            except Empty:
                pass
            else:
                conn = http.client.HTTPConnection(self.addr, port=self.port)
                body = {
                    "id": signal["id"],
                    "msg": {
                        "subnet-tag": signal["msg"]["subnet-tag"],
                        "sql": signal["msg"]["sql"],
                    },
                }
                body_as_json = json.dumps(body)
                try:
                    conn.request(
                        "GET",
                        "/",
                        body=body_as_json,
                        headers={"Content-Length": len(body_as_json)},
                    )
                except ConnectionRefusedError as e:
                    results_d = {
                        "id": signal["id"],
                        "msg": ["error", "connection refused"],
                    }
                else:
                    r1 = conn.getresponse()  # TODO make non-blocking
                    content = r1.read()
                    results_d = json.loads(
                        content.decode("utf-8")
                    )  # this is in the form { id, msg }
                if results_d:
                    self.q_out.put_nowait(results_d)
                else:
                    # revise to have view handle this! TODO
                    errormsg = (
                        "[LocalConnection::poll_loop] no results seen from callback"
                    )
                    print(errormsg, file=sys.stderr, flush=True)
            await asyncio.sleep(0.01)

    def __call__(self):
        asyncio.run(self.poll_loop())
