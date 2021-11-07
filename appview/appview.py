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
        """
        ss = "select 'node.id'.offerRowID, 'node.id'.name, 'inf.cpu'.architecture, 'inf.cpu'.capabilities, 'inf.cpu'.cores, 'inf.cpu'.model, 'inf.cpu'.threads, 'inf.cpu'.vendor, 'runtime'.name" \
            " FROM 'node.id' INNER JOIN 'inf.cpu' USING (offerRowID)" \
            " INNER JOIN 'runtime' USING (offerRowID)" \
            " WHERE 'runtime'.name = 'vm' " 
        """

        ss = "select 'node.id'.offerRowID, 'node.id'.name, 'inf.cpu'.architecture, 'inf.cpu'.capabilities, 'inf.cpu'.cores, 'inf.cpu'.model, 'inf.cpu'.threads, 'inf.cpu'.vendor, 'runtime'.name, 'offers'.hash, 'offers'.address, max('offers'.ts)" \
            " FROM 'node.id'" \
            " INNER JOIN 'inf.cpu'  USING (offerRowID)" \
            " INNER JOIN 'runtime'  USING (offerRowID)" \
            " INNER JOIN 'offers'   USING (offerRowID)" \
            " WHERE 'runtime'.name = 'vm' "  \
            " GROUP BY 'node.id'.name"  \
            " ORDER BY 'inf.cpu'.cores"
            # " ORDER BY 'offers'.ts"
            # " ORDER BY 'node.id'.name, 'offers'.ts DESC" \

        self.q_out.put_nowait({"id": next(self.gen_request_number), "msg": ss})

        while True:
            try:
                msg_in = self.q_in.get_nowait()
            except multiprocessing.queues.Empty:
                msg_in = None
            if msg_in:
                print(f"[AppView] got msg!")
                results = msg_in["msg"]
                for result in results:
                    # print(f"name: {result[1]}, architecture: {result[2]}, capabilities: {result[3]}, cores: {result[4]}, model: {result[5]}, threads: {result[6]}, vendor: {result[7]}")
                    print(f"name: {result[1]}, architecture: {result[2]}, cores: {result[4]}, model: {result[5]}, threads: {result[6]}, vendor: {result[7]}, hash: {result[9]}, address: {result[10]}, timestamp: {result[11]}\n")
                print(f"count: {len(results)}")
            time.sleep(0.01)
