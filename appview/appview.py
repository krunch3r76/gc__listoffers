# appview.py
import multiprocessing
from multiprocessing import Process, Queue
import itertools
from tkinter import *
from tkinter import ttk
from datetime import datetime
import decimal
from decimal import Decimal

from functools import partial

import time #debug


class AppView:
    def __init__(self):
        self.q_out=Queue()
        self.q_in=Queue()
        # self.gen_request_number = itertools.count(1)
        self.tree = None
        self.session_id='0'
        self.order_by_last="'node.id'.name"

        self.root=Tk()
        self.cpusec_entry = None
        self.cpusec_entry_var = StringVar()
        self.durationsec_entry = None
        self.durationsec_entry_var = StringVar()
        self.resultcount_var = StringVar(value="0")

        decimal.getcontext().prec=7




    def _update_cmd(self, *args):
        self.tree.delete(*self.tree.get_children())

        if len(args) > 0 and 'sort_on' in args[0]:
            self.order_by_last = args[0]['sort_on']

        ss = "select 'node.id'.offerRowID, 'node.id'.name, 'offers'.address, 'com.pricing.model.linear.coeffs'.cpu_sec, 'com.pricing.model.linear.coeffs'.duration_sec, 'com.pricing.model.linear.coeffs'.fixed, max('offers'.ts)" \
            " FROM 'node.id'" \
            " INNER JOIN 'offers' USING (offerRowID)" \
            " INNER JOIN 'com.pricing.model.linear.coeffs' USING (offerRowID)" \
            " INNER JOIN 'runtime'  USING (offerRowID)" \
            " WHERE 'runtime'.name = 'vm' " \

        if self.cpusec_entry.instate(['!disabled']) and self.cpusec_entry_var.get():
            ss+= f" AND 'com.pricing.model.linear.coeffs'.cpu_sec <= {Decimal(self.cpusec_entry_var.get())/Decimal(3600.0)}"

        if self.durationsec_entry.instate(['!disabled']) and self.durationsec_entry_var.get():
            ss+= f" AND 'com.pricing.model.linear.coeffs'.duration_sec <= {Decimal(self.durationsec_entry_var.get())/Decimal(3600.0)}"

        ss+=" GROUP BY 'node.id'.name"  \
            f" ORDER BY {self.order_by_last}"

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
            time.sleep(0.01)

        for result in results:
            result=list(result)
            self.tree.insert('', 'end', values=(result[1], result[2], Decimal(result[3])*Decimal(3600.0), Decimal(result[4])*Decimal(3600.0), result[5], result[6]))

        self.resultcount_var.set(str(len(results)))


    def _refresh_cmd(self, *args):
        self.tree.delete(*self.tree.get_children())


        ss = "select 'node.id'.offerRowID, 'node.id'.name, 'offers'.address, 'com.pricing.model.linear.coeffs'.cpu_sec, 'com.pricing.model.linear.coeffs'.duration_sec, 'com.pricing.model.linear.coeffs'.fixed, max('offers'.ts)" \
            " FROM 'node.id'" \
            " INNER JOIN 'offers' USING (offerRowID)" \
            " INNER JOIN 'com.pricing.model.linear.coeffs' USING (offerRowID)" \
            " INNER JOIN 'runtime'  USING (offerRowID)" \
            " WHERE 'runtime'.name = 'vm' "

        if self.cpusec_entry.instate(['!disabled']) and self.cpusec_entry_var.get():
            ss+= f" AND 'com.pricing.model.linear.coeffs'.cpu_sec <= {Decimal(self.cpusec_entry_var.get())/Decimal('3600.0')}"
         
        if self.durationsec_entry.instate(['!disabled']) and self.durationsec_entry_var.get():
            ss+= f" AND 'com.pricing.model.linear.coeffs'.duration_sec <= {Decimal(self.durationsec_entry_var.get())/Decimal(3600.0)}"

        ss+=" GROUP BY 'node.id'.name"  \
            f" ORDER BY {self.order_by_last}"

        print(ss)
        self.session_id=str(datetime.now().timestamp())
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
            time.sleep(0.01)
        print(len(results)) 
        for result in results:
            result=list(result)
            self.tree.insert('', 'end', values=(result[1], result[2], Decimal(result[3])*Decimal(3600.0), Decimal(result[4])*Decimal(3600.0), result[5], result[6]))

        self.resultcount_var.set(str(len(results)))




    def _cb_cpusec_checkbutton(self, *args):
        if self.cpusec_entry.instate(['disabled']):
            self.cpusec_entry.state(['!disabled'])
        else:
            self.cpusec_entry.state(['disabled'])

    def _cb_durationsec_checkbutton(self, *args):
        if self.durationsec_entry.instate(['disabled']):
            self.durationsec_entry.state(['!disabled'])
        else:
            self.durationsec_entry.state(['disabled'])

    def __call__(self):
        root=self.root
        root.title("Provider View")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        mainframe=ttk.Frame(root)
        mainframe.grid(column=0, row=0, sticky="news")
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        inputframe=ttk.Frame(root)
        inputframe.grid(column=0,row=2, sticky="news")

        statusframe=ttk.Frame(root)
        statusframe.grid(column=0,row=1, stick="news")

        #cpusec check
        ttk.Checkbutton(inputframe, text="max cpu(/sec)", command=self._cb_cpusec_checkbutton).grid(column=0,row=0, sticky="w")
        #cpusec entry
        self.cpusec_entry = ttk.Entry(inputframe,textvariable=self.cpusec_entry_var)
        self.cpusec_entry.state(['disabled'])
        self.cpusec_entry.grid(column=1,row=0,stick="w")

        #durationsec check
        ttk.Checkbutton(inputframe, text="max duration/sec)", command=self._cb_durationsec_checkbutton).grid(column=2,row=0,sticky="w")
        #durationsec entry
        self.durationsec_entry = ttk.Entry(inputframe,textvariable=self.durationsec_entry_var)
        self.durationsec_entry.state(['disabled'])
        self.durationsec_entry.grid(column=3,row=0,stick="w")
        
        ttk.Button(statusframe, text="Refresh", command=self._refresh_cmd).grid(column=0,row=0)
        ttk.Label(statusframe, text="count:").grid(column=1,row=0)
        ttk.Label(statusframe, textvariable=self.resultcount_var).grid(column=2,row=0)



        tree = ttk.Treeview(mainframe, columns=('name','address','cpu', 'duration', 'fixed'))
        self.tree = tree
        self.tree.grid(column=0,row=1, columnspan=2, sticky="news")
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


