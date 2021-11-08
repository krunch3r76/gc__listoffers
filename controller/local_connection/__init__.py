# from multiprocessing import Queue
from multiprocessing.queues import Empty
import asyncio

class LocalConnection(): # later make subclass of abstract ControllerConnection
    """Class for connecting view to local model"""
    def __init__(self, q_out, q_in, signal_cb):
        self.q_out = q_out
        self.q_in = q_in
        self.signal_cb = signal_cb

    async def poll_loop(self):
        """monitors and handles signals from q_in
        places results of handle in q_out"""
        results_d=None
        while True:
            try:
                signal = self.q_in.get_nowait()
            except Empty:
                signal = None
            if signal:
                print(f"[LocalConnection] handling signal {signal}")
                results_d = await self.signal_cb(signal["id"], signal["msg"])
                if results_d:
                    print(f"[LocalConnection] got a result back from the callback and placing in queue to view!")
                    # revise callback, results should contain the id, as is the case with the remote server TODO
                    msg_out = { "id": signal["id"], "msg": results_d }
                    self.q_out.put_nowait(msg_out)

                else:
                    errormsg="[LocalConnection::poll_loop] no results seen from callback"
                    print(errormsg, flush=True)
                    #raise "unhandled exception in LocalConnection.poll_loop" \
                    #    "no results from callback"
            await asyncio.sleep(0.01)

    def __call__(self):
        asyncio.run(self.poll_loop())

