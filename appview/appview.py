# appview.py
from multiprocessing import Process, Queue

class AppView:

    def __init__(self):
        self.q_out=Queue()
        self.q_in=Queue()

    def __call__(self):
        self.q_out.put_nowait({"id": "0", "msg": "select whatever"})
        while True:
            pass

