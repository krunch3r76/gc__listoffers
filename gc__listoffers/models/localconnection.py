# from multiprocessing import Queue
from multiprocessing.queues import Empty
import asyncio
import debug


class LocalConnection:  # later make subclass of abstract
    # ControllerConnection
    """Class for connecting view to local model"""

    # _-_-_-_- __init__ _-_-_-_-
    def __init__(self, pipe_child, signal_cb):
        """set callback (i.e. offerLookup) for incoming signals etc"""
        # self.pipe_parent = pipe_parent  # out to view
        self.pipe_child = pipe_child  # in from view
        self.signal_cb = signal_cb

    # _-_-_-_- _on_signal _-_-_-_-
    async def _on_signal(self, signal):
        """relay next signal that came over the queue from view
        to the handler and send result signal back to view
            id
            msg
                subnet-tag
                sql

        """
        # print(f"[LocalConnection] handling signal {signal}")
        results_l = await self.signal_cb(
            signal["id"], signal["msg"]["subnet-tag"], signal["msg"]["sql"],
            signal["msg"].get("manual-probe", False)
        )  # signal from view

        if results_l and len(results_l) > 0:
            if results_l[0] == "error" and results_l[1] == 401:
                msg = ["error", "invalid api key"]
                msg_out = {"id": signal["id"], "msg": msg}
                self.pipe_child.send(msg_out)
            elif results_l[0] == "error" and results_l[1] == 111:
                msg = ["error", "cannot connect to yagna"]
                msg_out = {"id": signal["id"], "msg": msg}
                self.pipe_child.send(msg_out)
            else:
                debug.dlog(
                    f"got a result back from the callback"
                    + " and placing in queue to view!"
                )
                # revise callback, results should contain the id,
                # as is the case with the remote server TODO
                results_ld = [ dict(result) for result in results_l ]
                msg_out = {"id": signal["id"], "msg": results_ld}
                self.pipe_child.send(msg_out)
        else:
            errormsg = "no results seen from callback"
            debug.dlog(errormsg, 1)
            msg = ["error", "no results"]
            msg_out = {"id": signal["id"], "msg": msg}
            self.pipe_child.send(msg_out)
            # raise "unhandled exception in \
            # LocalConnection.poll_loop" \
            #    "no results from callback"

    # _-_-_-_- poll_loop _-_-_-_-
    async def poll_loop(self):
        """bridge to local model: monitors and handles (model) signals
        from pipe_child (from view) places results of handle (model)
        in pipe_parent (to view)"""
        results_l = None
        while True:
            signal = None
            if self.pipe_child.poll():
                signal = self.pipe_child.recv()
                await self._on_signal(signal)

            await asyncio.sleep(0.01)

    # _-_-_-_- __call__ _-_-_-_-
    def __call__(self):
        """launches the asynchronous polling"""
        """ intended to run in an independent process """
        asyncio.run(self.poll_loop())
