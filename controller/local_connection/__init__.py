# from multiprocessing import Queue
from multiprocessing.queues import Empty
import asyncio
import debug

class LocalConnection(): # later make subclass of abstract ControllerConnection
    """Class for connecting view to local model"""
    def __init__(self, q_out, q_in, signal_cb):
        self.q_out = q_out # out to view
        self.q_in = q_in # in from view
        self.signal_cb = signal_cb

    async def poll_loop(self):
        """monitors and handles signals from q_in
        places results of handle in q_out"""
        results_l=None
        while True:
            try:
                signal = self.q_in.get_nowait()
            except Empty:
                signal = None
            if signal:
                # print(f"[LocalConnection] handling signal {signal}")
                results_l = await self.signal_cb(signal["id"], signal["msg"]["subnet-tag"], signal["msg"]["sql"]) # signal from view
                if results_l and len(results_l)>0:
                    if results_l[0]=='error' and results_l[1]==401:
                        msg=['error', 'invalid api key']
                        msg_out = { "id": signal["id"], "msg": msg }
                        self.q_out.put_nowait(msg_out)
                    else:
                        debug.dlog(f"got a result back from the callback and placing in queue to view!")
                        # revise callback, results should contain the id, as is the case with the remote server TODO
                        msg_out = { "id": signal["id"], "msg": results_l }
                        self.q_out.put_nowait(msg_out)
                else:
                    errormsg="no results seen from callback"
                    debug.dlog(errormsg,0)
                    msg=['error', 'no results']
                    msg_out = { "id": signal["id"], "msg": msg }
                    self.q_out.put_nowait(msg_out)
                    #raise "unhandled exception in LocalConnection.poll_loop" \
                    #    "no results from callback"
            await asyncio.sleep(0.01)

    def __call__(self):
        asyncio.run(self.poll_loop())

