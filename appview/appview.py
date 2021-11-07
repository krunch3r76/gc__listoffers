# appview.py
import multiprocessing
from multiprocessing import Process, Queue
import itertools
from tkinter import *
from tkinter import ttk
from datetime import datetime

from functools import partial

import time #debug


class AppView:
    def __init__(self):
        self.q_out=Queue()
        self.q_in=Queue()
        self.gen_request_number = itertools.count(1)
        self.tree = None
        self.session_id='0'
        self.order_by_last="'node.id'.name"
    def _update_cmd(self, *args):
        if len(args) > 0 and 'sort_on' in args[0]:
            self.order_by_last = args[0]['sort_on']

        ss = "select 'node.id'.offerRowID, 'node.id'.name, 'offers'.address, 'com.pricing.model.linear.coeffs'.cpu_sec, 'com.pricing.model.linear.coeffs'.duration_sec, 'com.pricing.model.linear.coeffs'.fixed, max('offers'.ts)" \
            " FROM 'node.id'" \
            " INNER JOIN 'offers' USING (offerRowID)" \
            " INNER JOIN 'com.pricing.model.linear.coeffs' USING (offerRowID)" \
            " INNER JOIN 'runtime'  USING (offerRowID)" \
            " WHERE 'runtime'.name = 'vm' "  \
            " GROUP BY 'node.id'.name"  \
            f" ORDER BY {self.order_by_last}"
            # " ORDER BY 'com.pricing.model.linear.coeffs'.cpu_sec"
        self.tree.delete(*self.tree.get_children())

        self.q_out.put_nowait({"id": self.session_id, "msg": ss})

        results=None
        msg_in = None
        while not msg_in:
            try:
                msg_in = self.q_in.get_nowait()
            except multiprocessing.queues.Empty:
                msg_in = None
            if msg_in:
                print(f"[AppView] got msg!")
                results = msg_in["msg"]
                print(msg_in["id"])
                # for result in results:
                    # result=list(result)
                    # print(f"name: {result[1]}, address: {result[2]}, cpu_hr: {result[3]*3600}, duration_hr: {result[4]*3600}, fixed: {result[5]}, timestamp: {result[6]}\n")
                # print(f"count: {len(results)}")
            time.sleep(0.01)

        print(f"[AppView::_update_cmd] length of args is {len(args)}")
        print(f"{args[0]}")
        print(f"[AppView::_update_cmd()] displaying {len(results)} results") 

        for result in results:
            result=list(result)
            self.tree.insert('', 'end', values=(result[1], result[2], result[3]*3600, result[4]*3600, result[5], result[6]))

    def _refresh_cmd(self, *args):
        self.tree.delete(*self.tree.get_children())


        ss = "select 'node.id'.offerRowID, 'node.id'.name, 'offers'.address, 'com.pricing.model.linear.coeffs'.cpu_sec, 'com.pricing.model.linear.coeffs'.duration_sec, 'com.pricing.model.linear.coeffs'.fixed, max('offers'.ts)" \
            " FROM 'node.id'" \
            " INNER JOIN 'offers' USING (offerRowID)" \
            " INNER JOIN 'com.pricing.model.linear.coeffs' USING (offerRowID)" \
            " INNER JOIN 'runtime'  USING (offerRowID)" \
            " WHERE 'runtime'.name = 'vm' "  \
            " GROUP BY 'node.id'.name"  \

        self.session_id=str(datetime.now().timestamp())
        self.q_out.put_nowait({"id": self.session_id, "msg": ss})
        # self.q_out.put_nowait({"id": next(self.gen_request_number), "msg": ss})
        results=None
        msg_in = None
        while not msg_in:
            try:
                msg_in = self.q_in.get_nowait()
            except multiprocessing.queues.Empty:
                msg_in = None
            if msg_in:
                print(f"[AppView] got msg!")
                results = msg_in["msg"]
                print(msg_in["id"])
                # for result in results:
                    # result=list(result)
                    # print(f"name: {result[1]}, address: {result[2]}, cpu_hr: {result[3]*3600}, duration_hr: {result[4]*3600}, fixed: {result[5]}, timestamp: {result[6]}\n")
                # print(f"count: {len(results)}")
            time.sleep(0.01)
        print(len(results)) 
        for result in results:
            result=list(result)
            self.tree.insert('', 'end', values=(result[1], result[2], result[3]*3600, result[4]*3600, result[5], result[6]))

    def __call__(self):
        root=Tk()       
        root.title("Provider View")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        mainframe=ttk.Frame(root)
        mainframe.grid(column=0, row=0, sticky="news")
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        ttk.Button(mainframe, text="Refresh", command=self._refresh_cmd).grid(column=1,row=2)
        ttk.Button(mainframe, text="test", command=self._update_cmd).grid(column=0,row=2)
        tree = ttk.Treeview(mainframe, columns=('name','address','cpu', 'duration', 'fixed'))
        self.tree = tree
        self.tree.grid(column=0,row=0, columnspan=2, sticky="news")
        tree.column('#0', width=0, stretch=NO)
        tree.heading('name', text='name'
                , command=lambda *args: self._update_cmd({"sort_on": "'node.id'.name"})
                )
        tree.heading('address', text='address'
                , command=lambda *args: self._update_cmd({"sort_on": "'offers'.address"})
                )
        tree.heading('cpu', text='cpu (/sec)'
                , command=lambda *args: self._update_cmd({"sort_on": "'com.pricing.model.linear.coeffs'.cpu_sec"})
                )
        tree.heading('duration', text='duration (/sec)'
                , command=lambda *args: self._update_cmd({"sort_on": "'com.pricing.model.linear.coeffs'.duration_sec"})
                )
        tree.heading('fixed', text='fixed'
                , command=lambda *args: self._update_cmd({"sort_on": "'com.pricing.model.linear.coeffs'.fixed"})
                )

        # tree.insert('', 'end', values=('namevalue', 'addressvalue', 'cpuvalue', 'durationvalue', 'fixedvalue'))
        root.mainloop()

    def __call___console(self):
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


        ss = "select 'node.id'.offerRowID, 'node.id'.name, 'offers'.address, 'com.pricing.model.linear.coeffs'.cpu_sec, 'com.pricing.model.linear.coeffs'.duration_sec, 'com.pricing.model.linear.coeffs'.fixed, max('offers'.ts)" \
            " FROM 'node.id'" \
            " INNER JOIN 'offers' USING (offerRowID)" \
            " INNER JOIN 'com.pricing.model.linear.coeffs' USING (offerRowID)" \
            " INNER JOIN 'runtime'  USING (offerRowID)" \
            " WHERE 'runtime'.name = 'vm' "  \
            " GROUP BY 'node.id'.name"  \


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
                    result=list(result)
                    # print(f"name: {result[1]}, architecture: {result[2]}, capabilities: {result[3]}, cores: {result[4]}, model: {result[5]}, threads: {result[6]}, vendor: {result[7]}")
                    # print(f"name: {result[1]}, architecture: {result[2]}, cores: {result[4]}, model: {result[5]}, threads: {result[6]}, vendor: {result[7]}, hash: {result[9]}, address: {result[10]}, timestamp: {result[11]}\n")
                    # print(f"name: {result[1]}, address: {result[2]}, cpu_sec: {result[3]}, cpu_duration: {result[4]}, fixed: {result[5]}, timestamp: {result[6]}\n")
                    print(f"name: {result[1]}, address: {result[2]}, cpu_hr: {result[3]*3600}, duration_hr: {result[4]*3600}, fixed: {result[5]}, timestamp: {result[6]}\n")
                print(f"count: {len(results)}")
            time.sleep(0.01)
