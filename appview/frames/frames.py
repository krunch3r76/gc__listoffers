from tkinter import *
from tkinter import ttk
import debug

DIC411 = "#003366"
DIC544 = "#4D4D4D"


class RefreshFrame:
    class RadioFrame:
        def __init__(self, master, *args, **kwargs):
            self.w = ttk.Frame(*args, **kwargs)
            self.master = master

            # create publicbeta_rb
            self.publicbeta_rb = ttk.Radiobutton(
                self.w,
                text="public-beta",
                variable=self.master.subnet_var,
                value="public-beta",
                command=self.master._refresh_cmd,
            )

            # create publicdevnet_rb
            self.publicdevnet_rb = ttk.Radiobutton(
                self.w,
                text="devnet-beta",
                variable=self.master.subnet_var,
                value="devnet-beta",
                command=self.master._refresh_cmd,
            )

            # create other_db
            self.other_rb = ttk.Radiobutton(
                self.w,
                text="other",
                value="other",
                variable=self.master.subnet_var,
                command=self.master._on_other_radio,
            )

            # create other_entry
            self.other_entry = ttk.Entry(
                self.w, textvariable=self.master.other_entry_var
            )
            self.other_entry.state(["disabled"])
            self.other_entry.bind("<Return>", lambda e: self.master._refresh_cmd())
            self.other_entry.bind("<FocusOut>", self.master._on_other_entry_focusout)
            self.other_entry.bind("<Button-1>", self.master._on_other_entry_click)

            self.w.rowconfigure(0, pad=5, weight=1)
            self.w.rowconfigure(1, weight=1)
            self.w.columnconfigure(0, weight=1)
            self.w.columnconfigure(1, weight=1)

            # grid components
            self.publicbeta_rb.grid(column=0, row=0, sticky="w")
            self.publicdevnet_rb.grid(column=1, row=0, sticky="w")
            self.other_rb.grid(column=0, row=1, sticky="w")
            self.other_entry.grid(column=1, row=1, sticky="w")

    def __init__(self, master, toggle_refresh_controls, *args, **kwargs):
        self.w = ttk.Frame(*args, **kwargs)
        self._toggle_refresh_controls = toggle_refresh_controls
        self.master = master

        self.refreshButton = ttk.Button(
            self.w, text="Refresh", command=self.master._refresh_cmd
        )

        self.radio_frame = self.RadioFrame(self.master, self.w)

        self.radio_frame.w["padding"] = (0, 5, 0, 5)

        self.w.columnconfigure(0, weight=1)
        self.w.rowconfigure(0, weight=1)
        self.w.rowconfigure(1, weight=1)

        self.refreshButton.grid(column=0, row=0, sticky=(W))
        self.radio_frame.w.grid(column=0, row=1, sticky=(W, N))


class CountFrame:
    def __init__(self, master, *args, **kwargs):
        self.master = master
        self.w = ttk.Frame(*args, **kwargs)

        self.count_label = ttk.Label(
            self.w,
            textvariable=self.master.resultcount_var,
            foreground=DIC544,
            font="TkDefaultFont 20",
        )
        self.count_diff_label = ttk.Label(
            self.w,
            textvariable=self.master.resultdiffcount_var,
            foreground=DIC544,
            font="TkDefaultFont 20",
        )

        self.count_label.grid(column=0, row=0, sticky="s")
        self.count_diff_label.grid(column=1, row=0)


class CPUSecFrame:
    """
    Groups the widgets for enabling and specifying max cpu/hr
    master: parent object (Appview)
    w:  widget (Frame)
    cbMaxCpuVar:    state of checkbutton {maxcpu, nomaxcpu}
    cb: checkbutton callback
    cpusec_entry:   Entry widget next to checkbutton
    """

    def __init__(self, master, *args, **kwargs):
        self.master = master
        self.w = ttk.Frame(*args, **kwargs)
        self.w["padding"] = (0, 0, 50, 0)

        self.cbMaxCpuVar = StringVar()
        self.cb = ttk.Checkbutton(
            self.w,
            text="max cpu(/hr)",
            command=self.master._cb_cpusec_checkbutton,
            onvalue="maxcpu",
            offvalue="nomaxcpu",
            variable=self.cbMaxCpuVar,
            padding=(0, 0, 5, 0),
        )

        self.cpusec_entry = ttk.Entry(
            self.w, textvariable=self.master.cpusec_entry_var, width=12
        )
        self.cpusec_entry.state(["disabled"])
        self.cpusec_entry.bind("<FocusOut>", lambda e: self.master._update_cmd())
        self.cpusec_entry.bind("<Return>", lambda e: self.master.root.focus_set())
        # self.cpusec_entry.bind('<Return>', lambda e: self.master._update_cmd())

        self.cb.grid(column=0, row=0, sticky="w")
        self.cpusec_entry.grid(column=1, row=0, stick="w")

    def refresh_entry_state(self):
        if self.cbMaxCpuVar.get() == "maxcpu":
            self.cpusec_entry.state(["!disabled"])
        else:
            self.cpusec_entry.state(["disabled"])

    def disable(self):
        self.cb.state(["disabled"])
        # self.refresh_entry_state()
        self.cpusec_entry.state(["disabled"])

    def enable(self):
        self.cb.state(["!disabled"])
        self.refresh_entry_state()
        # self.cpusec_entry.state(['!disabled'])


class DurSecFrame:
    def __init__(self, master, *args, **kwargs):
        self.master = master
        self.w = ttk.Frame(*args, **kwargs)

        self.cbDurSecVar = StringVar()
        self.cb = ttk.Checkbutton(
            self.w,
            text="max duration(/hr)",
            command=self.master._cb_durationsec_checkbutton,
            onvalue="maxdur",
            offvalue="nomaxdur",
            variable=self.cbDurSecVar,
            padding=(0, 0, 5, 0),
        )
        #     ...entry
        self.durationsec_entry = ttk.Entry(
            self.w, textvariable=self.master.durationsec_entry_var, width=12
        )
        self.durationsec_entry.state(["disabled"])
        self.durationsec_entry.bind("<FocusOut>", lambda e: self.master._update_cmd())
        self.durationsec_entry.bind("<Return>", lambda e: self.master.root.focus_set())
        # self.durationsec_entry.bind('<Return>', lambda e: self.master._update_cmd())

        self.cb.grid(column=0, row=0, sticky="w")
        self.durationsec_entry.grid(column=1, row=0, stick="w")

    def _refresh_entry_state(self):
        if self.cbDurSecVar.get() == "maxdur":
            self.durationsec_entry.state(["!disabled"])
        else:
            self.durationsec_entry.state(["disabled"])

    def disable(self):
        self.cb.state(["disabled"])
        self.durationsec_entry.state(["disabled"])

    def enable(self):
        self.cb.state(["!disabled"])
        self._refresh_entry_state()
        # self.durationsec_entry.state(['!disabled'])


class FeatureEntryFrame:
    def __init__(self, master, *args, **kwargs):
        self.master = master
        self.w = ttk.Frame(*args, **kwargs)

        self.cbFeatureEntryVar = StringVar()
        self.cb = ttk.Checkbutton(
            self.w,
            text="feature",
            command=self.master._cb_feature_checkbutton,
            onvalue="feature",
            offvalue="nofeature",
            variable=self.cbFeatureEntryVar,
            padding=(0, 0, 5, 0),
        )
        #     ...entry
        self.feature_entry = ttk.Entry(
            self.w, textvariable=self.master.featureEntryVar, width=12
        )
        self.feature_entry.state(["disabled"])
        self.feature_entry.bind("<FocusOut>", lambda e: self.master._update_cmd())
        self.feature_entry.bind("<Return>", lambda e: self.master.root.focus_set())
        # self.durationsec_entry.bind('<Return>', lambda e: self.master._update_cmd())

        self.cb.grid(column=0, row=0, sticky="w")
        self.feature_entry.grid(column=1, row=0, stick="w")

    def _refresh_entry_state(self):
        if self.cbFeatureEntryVar.get() == "feature":
            self.feature_entry.state(["!disabled"])
        else:
            self.feature_entry.state(["disabled"])

    def disable(self):
        self.cb.state(["disabled"])
        self.feature_entry.state(["disabled"])

    def enable(self):
        self.cb.state(["!disabled"])
        self._refresh_entry_state()
        # self.durationsec_entry.state(['!disabled'])
