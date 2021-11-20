from tkinter import *
from tkinter import ttk


DIC411="#003366"
DIC544="#4D4D4D"

class RefreshFrame():

    
    class RadioFrame():

        def __init__(self, master, *args, **kwargs):
            self.w = ttk.Frame(*args, **kwargs)
            self.master = master

            # create publicbeta_rb
            self.publicbeta_rb = ttk.Radiobutton(self.w, text='public-beta',
                    variable=self.master.subnet_var, value='public-beta', command=self.master._refresh_cmd)
           
            # create publicdevnet_rb
            self.publicdevnet_rb = ttk.Radiobutton(self.w, text='devnet-beta',
                    variable=self.master.subnet_var, value='devnet-beta', command=self.master._refresh_cmd)

            # create other_db
            self.other_rb = ttk.Radiobutton(self.w, text='other', value='other'
                    , variable=self.master.subnet_var, command=self.master._on_other_radio)

            # create other_entry
            self.other_entry = ttk.Entry(self.w, textvariable=self.master.other_entry_var)
            self.other_entry.state(['disabled'])
            self.other_entry.bind('<Return>', lambda e: self.master._refresh_cmd())
            self.other_entry.bind('<FocusOut>', self.master._on_other_entry_focusout)
            self.other_entry.bind('<Button-1>', self.master._on_other_entry_click)

            # grid components
            self.publicbeta_rb.grid(    column=0,row=0)
            self.publicdevnet_rb.grid(  column=1,row=0)
            self.other_rb.grid(         column=0,row=1, sticky="w")
            self.other_entry.grid(      column=1,row=1, sticky="w")




    def __init__(self, master, toggle_refresh_controls, *args, **kwargs):   
        self.w = ttk.Frame(*args, **kwargs)
        self._toggle_refresh_controls = toggle_refresh_controls
        self.master = master

        # self.w.grid(column=0, row=1, sticky="e")
        self.w.columnconfigure(0, weight=0)
        self.w.columnconfigure(1, weight=0)
        self.w.columnconfigure(2, weight=1)
        self.w['padding']=(0,0,0,10)
        
        self.refreshButton = ttk.Button(self.w, text="Refresh", command=self.master._refresh_cmd)

        self.radio_frame=self.RadioFrame(self.master, self.w)

        self.refreshButton.grid(column=0,row=0,sticky="w,e")
        self.radio_frame.w.grid(column=0,row=1)




class CountFrame():
    def __init__(self, master, *args, **kwargs):
        self.master=master
        self.w = ttk.Frame(*args, **kwargs)

        self.count_label = ttk.Label(self.w, textvariable=self.master.resultcount_var, foreground=DIC544, font='TkDefaultFont 20')
        self.count_diff_label = ttk.Label(self.w, textvariable=self.master.resultdiffcount_var, foreground=DIC544, font='TkDefaultFont 20')

        self.count_label.grid(column=1,row=1)
        self.count_diff_label.grid(column=2,row=1)




class CPUSecFrame():
    def __init__(self, master, *args, **kwargs):
        self.master=master
        self.w = ttk.Frame(*args, **kwargs)
        self.w['padding']=(0,0,50,0)

        self.cbMaxCpuVar = StringVar()
        self.cb= ttk.Checkbutton(self.w, text="max cpu(/sec)", command=self.master._cb_cpusec_checkbutton, onvalue='maxcpu', offvalue='nomaxcpu', variable=self.cbMaxCpuVar, padding=(0,0,5,0))
        
        self.cpusec_entry = ttk.Entry(self.w,textvariable=self.master.cpusec_entry_var,width=12)
        self.cpusec_entry.state(['disabled'])
        self.cpusec_entry.bind('<FocusOut>', lambda e: self.master._update_cmd())
        self.cpusec_entry.bind('<Return>', lambda e: self.master.root.focus_set())

        self.cb.grid(           column=0,row=0, sticky="w")
        self.cpusec_entry.grid( column=1,row=0,stick="w")


class DurSecFrame():
    def __init__(self, master, *args, **kwargs):
        self.master=master
        self.w=ttk.Frame(*args, **kwargs)

        self.cbDurSecVar=StringVar()
        self.cb=ttk.Checkbutton(self.w, text="max duration(/sec)", command=self.master._cb_durationsec_checkbutton, variable=self.cbDurSecVar, padding=(0,0,5,0))
        #     ...entry
        self.durationsec_entry = ttk.Entry(self.w,textvariable=self.master.durationsec_entry_var, width=12)
        self.durationsec_entry.state(['disabled'])
        self.durationsec_entry.bind('<FocusOut>', lambda e: self.master._update_cmd())
        self.durationsec_entry.bind('<Return>', lambda e: root.master.focus_set())

        self.cb.grid(column=0,row=0,sticky="w")
        self.durationsec_entry.grid(column=1,row=0,stick="w")

