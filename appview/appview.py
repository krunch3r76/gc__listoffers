# appview.py
import multiprocessing
from multiprocessing import Process, Queue
import itertools
import time #debug
class AppView:
    def __init__(self):
        self.q_out=Queue()
        self.q_in=Queue()
        self.gen_request_number = itertools.count(1)
    def __call__(self):
        self.q_out.put_nowait({"id": next(self.gen_request_number), "msg": "select * from node.id"})

        while True:
            try:
                msg_in = self.q_in.get_nowait()
            except multiprocessing.queues.Empty:
                msg_in = None
            if msg_in:
                print(msg_in)
            time.sleep(0.01)
