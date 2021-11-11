



# appview.py
import multiprocessing
from multiprocessing import Process, Queue
import itertools
from tkinter import *
from tkinter import ttk
from datetime import datetime
import decimal
from decimal import Decimal
import json
import debug

# from functools import partial

import time #debug

DIC411="#003366"
DIC544="#4D4D4D"



def _toggle_refresh_controls_closure(self):
    disabled = False
    def toggle():
        nonlocal disabled
        if not disabled:
            self.refreshButton.state(['disabled'])
            self.publicbeta_rb.state(['disabled'])
            self.publicdevnet_rb.state(['disabled'])
            disabled=True
        else:
            self.refreshButton.state(['!disabled'])
            self.publicbeta_rb.state(['!disabled'])
            self.publicdevnet_rb.state(['!disabled'])

    return toggle




class AppView:
    def __init__(self):
        self._toggle_refresh_controls = _toggle_refresh_controls_closure(self)

        self.q_out=Queue()
        self.q_in=Queue()
        self.tree = None
        self.session_id=None
        self.order_by_last="'node.id'.name"

        self.root=Tk()
        s = ttk.Style()
        self.root.tk.call('source', './forest-ttk-theme/forest-light.tcl')
        s.theme_use('forest-light')

        self.cpusec_entry = None
        self.cpusec_entry_var = StringVar()
        self.durationsec_entry = None
        self.durationsec_entry_var = StringVar()
        self.resultcount_var = StringVar(value="0")
        self.resultdiffcount_var = StringVar(value="")
        self.session_resultcount = None
        self.subnet_var = StringVar()
        self.cursorOfferRowID = None
        self.lastresultcount = 0
        decimal.getcontext().prec=7

        self.refreshButton=None
        self.publicbeta_rb=None
        self.publicdevnet_rb=None
        self.other_rb=None
        self.other_entry = None
        self.other_entry_var = StringVar()

    def _on_other_entry_focusout(self, *args):
        subnet=self.subnet_var.get()
        if subnet != 'public-beta' and subnet != 'devnet-beta':
            self.other_entry.state(['disabled'])

    def _on_other_entry_click(self, *args):
        subnet=self.subnet_var.get()
        if subnet != 'public-beta' and subnet != 'devnet-beta':
            self.other_entry.state(['!disabled'])

    def _on_other_radio(self, *args):
        self.other_entry.state(['!disabled'])
        self.subnet_var.set( self.other_entry_var.get() )
        self.other_rb['value']= self.other_entry_var.get()

    def _show_raw(self, *args):
        ss = f"select json from extra WHERE offerRowID = {self.cursorOfferRowID}"
        # review the need to pass subnet-tag on update TODO
        self.q_out.put_nowait({ "id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} })

        results=None
        msg_in = None
        while not msg_in:
            try:
                msg_in = self.q_in.get_nowait()
            except multiprocessing.queues.Empty:
                msg_in = None
            if msg_in:
                # print(f"[AppView] got msg!")
                results = msg_in["msg"]
                # print(msg_in["id"])
            time.sleep(0.1)
        results_json = json.loads(results[0][0])
        props=results_json["props"]
        props_s = json.dumps(props, indent=5)
        # create a new window
        t = Toplevel(self.root)        
        t.columnconfigure(0, weight=1)
        t.rowconfigure(0, weight=1)
        f = ttk.Frame(t)
        f.grid(column=0, row=0, sticky="news")
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        txt = Text(f)
        txt.grid(column=0, row=0, sticky="news")
        txt.insert('1.0', props_s)
        txt.configure(state='disabled')







    def _update(self, results, refresh=True):
        if refresh:
            self.session_resultcount=len(results)
        for result in results:
            result=list(result)
            self.tree.insert('', 'end', values=(result[0], result[1], result[2], Decimal(result[3])*Decimal(3600.0), Decimal(result[4])*Decimal(3600.0), result[5], result[6]))

        current_resultcount=len(results)
        self.resultcount_var.set(str(current_resultcount))
        
        if not refresh:
            disp=""
            if self.lastresultcount != 0 and self.session_resultcount != current_resultcount:
                disp+="/" + str(self.session_resultcount) + "("
                diff =  current_resultcount - self.lastresultcount
                POS=False
                if diff >0:
                    disp+="+"
                disp+=str(current_resultcount - self.lastresultcount) + ")"
                self.resultdiffcount_var.set(disp)
                # self.resultcount_var.set(str(new_resultcount))
            else:
                self.resultdiffcount_var.set("") # consider edge cases




        self._toggle_refresh_controls()





    def _update_cmd(self, *args):
        self._toggle_refresh_controls()

        if self.resultcount_var.get() != "":
            self.lastresultcount=int(self.resultcount_var.get())
        else:
            self.lastresultcount=0

        self.resultcount_var.set("")
        self.resultdiffcount_var.set("")

        self.tree.delete(*self.tree.get_children())
        if not self.session_id:
            return

        if len(args) > 0 and 'sort_on' in args[0]:
            self.order_by_last = args[0]['sort_on']

        ss = self._update_or_refresh_sql()

        # TODO remove subnet-tag, it is already associated with the id
        self.q_out.put_nowait({"id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} })

        results=None
        msg_in = None

        self.root.after(1, lambda: self.handle_incoming_result(False))






    def _update_or_refresh_sql(self):
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


        return ss







    def _refresh_cmd(self, *args):
        self._toggle_refresh_controls()

        self.resultcount_var.set("")
        self.resultdiffcount_var.set("")
        self.tree.delete(*self.tree.get_children())
        self.tree.update_idletasks()

        ss = self._update_or_refresh_sql()

        self.session_id=str(datetime.now().timestamp())
        msg_out = {"id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} }
        self.q_out.put_nowait({"id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} })
        results=None
        msg_in = None

        self.root.after(1, self.handle_incoming_result)







    def handle_incoming_result(self, refresh=True):
        try:
            msg_in = self.q_in.get_nowait()
        except multiprocessing.queues.Empty:
            msg_in = None
            self.root.after(1, lambda: self.handle_incoming_result(refresh))
        if msg_in:
            # print(f"[AppView] got msg!")
            results = msg_in["msg"]
            self._update(results, refresh)
            # print(msg_in["id"])
    # print(len(results)) 







    def _cb_cpusec_checkbutton(self, *args):
        if self.cpusec_entry.instate(['disabled']):
            self.cpusec_entry.state(['!disabled'])
        else:
            self.cpusec_entry.state(['disabled'])
        if self.cpusec_entry.get():
            self._update_cmd()




    def _cb_durationsec_checkbutton(self, *args):
        if self.durationsec_entry.instate(['disabled']):
            self.durationsec_entry.state(['!disabled'])
        else:
            self.durationsec_entry.state(['disabled'])
        if self.durationsec_entry.get():
            self._update_cmd()





    def __call__(self):
        root=self.root
        style=ttk.Style()
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
        refreshframe.grid(column=0,row=1, stick="e")
        refreshframe.columnconfigure(0, weight=0)
        refreshframe.columnconfigure(1, weight=0)
        refreshframe.columnconfigure(2, weight=1)
        refreshframe['padding']=(0, 0, 0, 10)



        # radio
        radio_frame=ttk.Frame(refreshframe)
        radio_frame.grid(column=0,row=0,sticky="w", pady=10)
        #       ...publicbeta
        self.publicbeta_rb = ttk.Radiobutton(radio_frame, text='public-beta', variable=self.subnet_var, value='public-beta', command=self._refresh_cmd)
        self.subnet_var.set('public-beta')
        self.publicbeta_rb.grid(column=0,row=0)
        #       ...devnetbeta
        self.publicdevnet_rb = ttk.Radiobutton(radio_frame, text='devnet-beta', variable=self.subnet_var, value='devnet-beta',command=self._refresh_cmd)
        self.publicdevnet_rb.grid(column=1,row=0)
        
        #       ...other
        self.other_rb = ttk.Radiobutton(radio_frame, text='other', value='other', variable=self.subnet_var, command=self._on_other_radio)
        self.other_rb.grid(column=0,row=1, sticky="w")
        self.other_entry_var.set('devnet-beta.2')
        self.other_entry = ttk.Entry(radio_frame, textvariable=self.other_entry_var)
        self.other_entry.grid(column=1,row=1, sticky="w")
        self.other_entry.state(['disabled'])
        self.other_entry.bind('<Return>', lambda e: self._refresh_cmd())
        self.other_entry.bind('<FocusOut>', self._on_other_entry_focusout)
        self.other_entry.bind('<Button-1>', self._on_other_entry_click)
        # refresh button
        self.refreshButton = ttk.Button(refreshframe, text="Refresh", command=self._refresh_cmd)
        self.refreshButton.grid(column=0,row=1,sticky="w,e")

        # count
        count_frame=ttk.Frame(subframe)
        count_frame.grid(column=1,row=1, sticky="e")
        # TkDefaultFont 10
        count_label = ttk.Label(count_frame, textvariable=self.resultcount_var, foreground=DIC544, font='TkDefaultFont 20')
        count_label.grid(column=1,row=1)
        count_diff_label = ttk.Label(count_frame, textvariable=self.resultdiffcount_var, foreground=DIC544, font='TkDefaultFont 20')
        count_diff_label.grid(column=2,row=1)
        # TLabel
        #style.configure('TLabel', )

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
        self.cpusec_entry.bind('<FocusOut>', lambda e: self._update_cmd())
        self.cpusec_entry.bind('<Return>', lambda e: root.focus_set())
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
        self.durationsec_entry.bind('<FocusOut>', lambda e: self._update_cmd())
        self.durationsec_entry.bind('<Return>', lambda e: root.focus_set())
        


        style.configure("Treeview.Heading", foreground=DIC411)
        tree = ttk.Treeview(mainframe, columns=('offerRowID', 'name','address','cpu', 'duration', 'fixed'))
        self.tree = tree

        root.option_add('*tearOff', FALSE)



        menu = Menu(root)
        menu.add_command(label='<name>')
        menu.entryconfigure(0, state=DISABLED)
        menu.add_separator()
        menu.add_command(label='view raw', command=self._show_raw)
        menu.add_command(label='exit menu')
        def do_popup(event):
            try:
                # identify the coordinates of tree
                # print(tree.state())
                if 'hover' not in tree.state():
                # if tree.state()[0] != 'hover':
                    return
                region = tree.identify_region(event.x, event.y)
                if region != 'cell':
                    menu.grab_release()
                    return
                # print(f"{tree.item( tree.identify_row(event.y) )['values']}")
                menu.entryconfigure(0, label=tree.item( tree.identify_row(event.y) )['values'][1])
                self.cursorOfferRowID=tree.item( tree.identify_row(event.y) )['values'][0]
                menu.post(event.x_root, event.y_root)
            except IndexError:
                pass
            finally:
                menu.grab_release()
        # root.bind('<ButtonRelease-3>', do_popup )
        if (root.tk.call('tk', 'windowingsystem')=='aqua'):
            root.bind('<2>', do_popup)
            root.bind('<Control-1>', do_popup)
        else:
            root.bind('<3>', do_popup )

        # tree.tag_configure('Theading', background='green')
        self.tree.grid(column=0,row=0, columnspan=2, sticky="news")
        tree.column('#0', width=0, stretch=NO)
        tree.column('offerRowID', width=0, stretch=NO)
        tree.heading('name', text='name', anchor="w" 
                , command=lambda *args: self._update_cmd({"sort_on": "'node.id'.name"})
                )
        tree.heading('address', text='address', anchor="w"
                , command=lambda *args: self._update_cmd({"sort_on": "'offers'.address"})
                )
        tree.heading('cpu', text='cpu (/sec)', anchor="w"
                , command=lambda *args: self._update_cmd({"sort_on": "'com.pricing.model.linear.coeffs'.cpu_sec"})
                )
        tree.heading('duration', text='duration (/sec)', anchor="w"
                , command=lambda *args: self._update_cmd({"sort_on": "'com.pricing.model.linear.coeffs'.duration_sec"})
                )
        tree.heading('fixed', text='fixed', anchor="w"
                , command=lambda *args: self._update_cmd({"sort_on": "'com.pricing.model.linear.coeffs'.fixed"})
                )

        # tree.insert('', 'end', values=('namevalue', 'addressvalue', 'cpuvalue', 'durationvalue', 'fixedvalue'))
        root.mainloop()


