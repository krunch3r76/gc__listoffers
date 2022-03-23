# from multiprocessing import Queue
from multiprocessing.queues import Empty
import asyncio
import debug


class LocalConnection:  # later make subclass of abstract
    # ControllerConnection
    """Class for connecting view to local model"""

    # _-_-_-_- __init__ _-_-_-_-
    def __init__(self, q_out, q_in, signal_cb):
        """set callback (i.e. offerLookup) for incoming signals etc"""
        self.q_out = q_out  # out to view
        self.q_in = q_in  # in from view
        self.signal_cb = signal_cb

    # _-_-_-_- _on_signal _-_-_-_-
    async def _on_signal(self, signal):
        """relay next signal that came over the queue from view
        to the handler and send result signal back to view"""
        # print(f"[LocalConnection] handling signal {signal}")
        results_l = await self.signal_cb(
            signal["id"], signal["msg"]["subnet-tag"], signal["msg"]["sql"],
            signal["msg"]["manual-probe"]
        )  # signal from view

        if results_l and len(results_l) > 0:
            if results_l[0] == "error" and results_l[1] == 401:
                msg = ["error", "invalid api key"]
                msg_out = {"id": signal["id"], "msg": msg}
                self.q_out.put_nowait(msg_out)
            elif results_l[0] == "error" and results_l[1] == 111:
                msg = ["error", "cannot connect to yagna"]
                msg_out = {"id": signal["id"], "msg": msg}
                self.q_out.put_nowait(msg_out)
            else:
                debug.dlog(
                    f"got a result back from the callback"
                    + " and placing in queue to view!"
                )
                # revise callback, results should contain the id,
                # as is the case with the remote server TODO
                msg_out = {"id": signal["id"], "msg": results_l}
                self.q_out.put_nowait(msg_out)
        else:
            errormsg = "no results seen from callback"
            debug.dlog(errormsg, 1)
            msg = ["error", "no results"]
            msg_out = {"id": signal["id"], "msg": msg}
            self.q_out.put_nowait(msg_out)
            # raise "unhandled exception in \
            # LocalConnection.poll_loop" \
            #    "no results from callback"

    # _-_-_-_- poll_loop _-_-_-_-
    async def poll_loop(self):
        """bridge to local model: monitors and handles (model) signals
        from q_in (from view) places results of handle (model)
        in q_out (to view)"""
        results_l = None
        while True:
            try:
                signal = self.q_in.get_nowait()
            except Empty:
                signal = None

            if signal:
                await self._on_signal(signal)

            await asyncio.sleep(0.01)

    # _-_-_-_- __call__ _-_-_-_-
    def __call__(self):
        """launches the asynchronous polling"""
        """ intended to run in an independent process """
        asyncio.run(self.poll_loop())
