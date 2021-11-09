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
        self.subnet_var = StringVar()
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

        self.q_out.put_nowait({"id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} })

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
            time.sleep(0.1)

        for result in results:
            result=list(result)
            self.tree.insert('', 'end', values=(result[1], result[2], Decimal(result[3])*Decimal(3600.0), Decimal(result[4])*Decimal(3600.0), result[5], result[6]))

        self.resultcount_var.set(str(len(results)))


    def _refresh_cmd(self, *args):
        self.tree.delete(*self.tree.get_children())
        self.tree.update_idletasks()


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

        # print(ss)
        self.session_id=str(datetime.now().timestamp())
        msg_out = {"id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} }
        # print(f"[appview.py] {msg_out})")
        self.q_out.put_nowait({"id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} })
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
            time.sleep(0.1)
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
        mainframe['padding']=(0,0,0,10)

        subframe=ttk.Frame(root)
        subframe.grid(column=0, row=1, sticky="news")
        subframe.rowconfigure(0, weight=1)
        subframe['padding']=(10)
        # subframe['padding']=(0,0,0,10)

        refreshframe=ttk.Frame(subframe)
        refreshframe.grid(column=0,row=1, stick="news")
        refreshframe.columnconfigure(0, weight=0)
        refreshframe.columnconfigure(1, weight=0)
        refreshframe.columnconfigure(2, weight=1)
        refreshframe['padding']=(0, 0, 0, 10)



        # radio
        radio_frame=ttk.Frame(refreshframe)
        radio_frame.grid(column=0,row=0,stick="w")
        #       ...publicbeta
        publicbeta_rb = ttk.Radiobutton(radio_frame, text='public-beta', variable=self.subnet_var, value='public-beta', command=self._refresh_cmd)
        self.subnet_var.set('public-beta')
        publicbeta_rb.grid(column=0,row=0)
        #       ...devnetbeta
        ttk.Radiobutton(radio_frame, text='devnet-beta', variable=self.subnet_var, value='devnet-beta',command=self._refresh_cmd).grid(column=1,row=0)
        
        # refresh button
        ttk.Button(refreshframe, text="Refresh", command=self._refresh_cmd).grid(column=0,row=1,sticky="w,e")

        # count
        count_frame=ttk.Frame(subframe)
        count_frame.grid(column=1,row=1, sticky="w")
        ttk.Label(count_frame, text="count:", padding=(0,0,0,0)).grid(column=1,row=1, sticky="w")
        ttk.Label(count_frame, textvariable=self.resultcount_var).grid(column=2,row=1, sticky="w")


        #cpusec
        cpusec_entryframe=ttk.Frame(subframe)
        cpusec_entryframe.grid(column=0,row=2,stick="w")
        cpusec_entryframe['padding']=(0,0,50,0)
        #cpusec .check
        cbMaxCpuVar = StringVar()
        ttk.Checkbutton(cpusec_entryframe, text="max cpu(/sec)", command=self._cb_cpusec_checkbutton, onvalue='maxcpu', offvalue='nomaxcpu', variable=cbMaxCpuVar, padding=(0,0,5,0)).grid(column=0,row=0, sticky="w")
        #     ...entry
        self.cpusec_entry = ttk.Entry(cpusec_entryframe,textvariable=self.cpusec_entry_var,width=12)
        self.cpusec_entry.state(['disabled'])
        self.cpusec_entry.grid(column=1,row=0,stick="w")

        #dursec
        dursec_entryframe=ttk.Frame(subframe)
        dursec_entryframe.grid(column=1,row=2,stick="w")
        #dursec .check
        cbDurSecVar=StringVar()
        ttk.Checkbutton(dursec_entryframe, text="max duration(/sec)", command=self._cb_durationsec_checkbutton, variable=cbDurSecVar, padding=(0,0,5,0)).grid(column=0,row=0,sticky="w")
        #     ...entry
        self.durationsec_entry = ttk.Entry(dursec_entryframe,textvariable=self.durationsec_entry_var, width=12)
        self.durationsec_entry.state(['disabled'])
        self.durationsec_entry.grid(column=1,row=0,stick="w")
        



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


