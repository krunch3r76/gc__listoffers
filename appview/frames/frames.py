from tkinter import *
from tkinter import ttk
import debug
from pprint import pprint, pformat

DIC411 = "#003366"
DIC544 = "#4D4D4D"

class RadioFrame:

    def on_other_entry_focusout(self, *args):
        subnet = self.appView.subnet_var.get()

        if subnet != "public-beta" and subnet != "devnet-beta":
            # self.refreshFrame.radio_frame.other_entry.state(["disabled"])
            self.other_entry.state(["disabled"])

    def on_other_entry_click(self, *args):
        subnet = self.appView.subnet_var.get()

        if self.other_rb.instate(["!disabled"]):
            subnet = self.appView.subnet_var.get()
            if subnet != "public-beta" and subnet != "devnet-beta":
                # self.refreshFrame.radio_frame.other_entry.state(["!disabled"])
                self.other_entry.state(["!disabled"])

    def on_other_entry_change(self, *args):
        """ updates subnet variable """
        # probably should just check the value on refresh
        self.other_rb["value"] = self.other_entry_var.get()
        self.appView.subnet_var.set(self.other_entry_var.get())


    def on_other_radio(self, *args):
        """ store text in other entry field into subnet variable """
        # probably should just check the value on refresh or trigger refresh
        self.other_entry.state(["!disabled"])
        # debug.dlog(self.other_entry_var.get() )
        self.other_rb["value"] = self.other_entry_var.get()
        self.appView.subnet_var.set(self.other_entry_var.get())


    # RadioFrame __init__
    # def __init__(self, master):

    def __init__(self, appView, refreshFrame):
        self.appView = appView
        self.refreshFrame = refreshFrame
        self.w = ttk.Frame(self.refreshFrame.w)
        self.master = self.appView.refreshFrame
        self.other_entry_var = StringVar()
        # self.refreshFrame = refreshFrame

        # create publicbeta_rb
        self.publicbeta_rb = ttk.Radiobutton(
            self.w,
            text="public-beta",
            variable=self.appView.subnet_var,
            value="public-beta",
            command=self.appView._refresh_cmd,
        )

        # create publicdevnet_rb
        self.publicdevnet_rb = ttk.Radiobutton(
            self.w,
            text="devnet-beta",
            variable=self.appView.subnet_var,
            value="devnet-beta",
            command=self.appView._refresh_cmd,
        )

        # create other_db
        self.other_rb = ttk.Radiobutton(
            self.w,
            text="other",
            value="other",
            variable=self.appView.subnet_var,
            command=self.on_other_radio,
        )

        # create other_entry
        self.other_entry = ttk.Entry(
            self.w, textvariable=self.other_entry_var
        )
        self.other_entry.state(["disabled"])
        self.other_entry.bind("<Return>", lambda e: self.appView._refresh_cmd())
        self.other_entry.bind("<FocusOut>", self.on_other_entry_focusout)
        self.other_entry.bind("<Button-1>", self.on_other_entry_click)

        self.w.rowconfigure(0, pad=5, weight=1)
        self.w.rowconfigure(1, weight=1)
        self.w.columnconfigure(0, weight=1)
        self.w.columnconfigure(1, weight=1)

        # grid components
        self.publicbeta_rb.grid(column=0, row=0, sticky="w")
        self.publicdevnet_rb.grid(column=1, row=0, sticky="w")
        self.other_rb.grid(column=0, row=1, sticky="w")
        self.other_entry.grid(column=1, row=1, sticky="w")

        self.other_entry_var.set("devnet-beta.2")
        self.other_entry_var.trace_add("write", self.on_other_entry_change)

class RefreshFrame:
    #   _toggle_refresh_controls() {ref}
    #   w
    #   master
    #   refreshButton
    #   radio_frame



    # ----------------------------------------------------------------------- #
    #   RefreshFrame::  __init__
    # ----------------------------------------------------------------------- #
    def __init__(self, appView, toggle_refresh_controls, *args, **kwargs):
        self.w = ttk.Frame(*args, **kwargs)
        self._toggle_refresh_controls = toggle_refresh_controls
        self.appView = appView

        self.refreshButton = ttk.Button(
            self.w, text="Refresh", command=self.appView._refresh_cmd
        )

        self.updateButton = ttk.Button(
            self.w, text="Update", command=self.appView._update_cmd
        )

        # self.radio_frame = self.appView.radioFrame

        # self.radio_frame = self.RadioFrame(refreshFrame=self, appView=self.master)


        self.w.columnconfigure(0, weight=0)
        self.w.columnconfigure(1, weight=0)
        self.w.columnconfigure(2, weight=0)
        self.w.rowconfigure(0, weight=1)
        self.w.rowconfigure(1, weight=1)

        self.refreshButton.grid(column=0, row=0, sticky=(W))
        self.updateButton.grid(column=1, row=0, sticky=(W))



class CountFrame:
    def __init__(self, master, *args, **kwargs):
        def _debug_enable_border(wid):
            wid["borderwidth"] = 2
            wid["relief"] = "solid"

        if not master.DARKMODE:
            foregroundcolor = DIC544
        else:
            foregroundcolor = "#eeeeee"

        self.master = master
        self.w = ttk.Frame(*args, **kwargs)
        self.resultcount_var = StringVar()
        self.glmcount1_var = StringVar()
        self.glmcount2_var = StringVar()
        # debug
        self.glmcount1_var.set("0")
        self.glmcount2_var.set("0")
        self.resultcount_var.set("0")
        self.w.rowconfigure(0, weight=1)
        self.w.rowconfigure(1, weight=1)
        self.w.columnconfigure(0, weight=1)
        self.w.columnconfigure(1, weight=0)
        self.w.columnconfigure(2, weight=1)
        self.count_label = ttk.Label(
            self.w,
            textvariable=self.resultcount_var,
            foreground=foregroundcolor,
            font="TkDefaultFont 20",
        )

        self.glmcount1_label = ttk.Label(
            self.w, textvariable=self.glmcount1_var, font="TkDefaultFont 10"
        )
        self.glmcount2_label = ttk.Label(
            self.w,
            textvariable=self.glmcount2_var,
            font="TkDefaultFont 10",
        )

        self.glmcount_separator = ttk.Label(self.w, text="|", font="TkDefaultFont 10")

        # self.resultcount_var.trace_add("write", lambda *args: print("it has been written"))

        self.count_label.grid(column=0, columnspan=3, row=0, sticky="n")
        self.glmcount1_label.grid(column=0, row=1, sticky="w")
        self.glmcount_separator.grid(column=1, row=1, sticky="")
        self.glmcount2_label.grid(column=2, row=1, sticky="e")
        # self.count_diff_label.grid(column=1, row=0)

    # primary_currency may be deprecated soon
    def update_counts(self, total, primary, secondary, primary_currency=""):
        self.resultcount_var.set(total)
        self.glmcount1_var.set(primary)
        self.glmcount_separator.configure(text="|")
        self.glmcount2_var.set(secondary)

    def clear_counts(self):
        self.resultcount_var.set("")
        self.glmcount1_var.set("")
        self.glmcount_separator.configure(text="")
        self.glmcount2_var.set("")


class FilterFrame(ttk.Frame):
    """base class for filter frames"""

    def __init__(self, master, widgetRoot, text, cmd, entryDefault=None):
        if entryDefault == None:
            entryDefault = ""
        self._master = master
        super().__init__(widgetRoot)
        self._cbVar = BooleanVar()
        self.entryVar = StringVar()
        self.entryVar.set(entryDefault)
        self.cb = ttk.Checkbutton(
            self,
            text=text,
            padding=(0, 0, 5, 0),
            variable=self._cbVar,
            command=cmd,
            onvalue=True,
            offvalue=False,
        )
        # self.cb.state(["!alternate", "!selected"])
        self.entry = ttk.Entry(self, textvariable=self.entryVar, width=12)
        self.entry.state(["disabled"])
        self.cb.grid(column=0, row=0, sticky="w")
        self.entry.grid(column=1, row=0, sticky="w")

        self.entry.bind("<FocusOut>", lambda e: self._master._update_cmd())
        self.entry.bind("<Return>", lambda e: self._master.root.focus_set())

    def disable(self):
        self.cb.state(["disabled"])
        self.refresh_entry_state()

    def enable(self):
        self.cb.state(["!disabled"])
        self.refresh_entry_state()

    def refresh_entry_state(self):
        if self.cb.instate(["!disabled"]):
            self.entry.state(["!disabled"])
        else:
            self.entry.state(["disabled"])

    def _cmd(self):
        if self.whether_checked:
            self.entry.state(["!disabled"])
        else:
            self.entry.state(["disabled"])
            self._master._update_cmd()

    @property
    def whether_checked(self):
        return self._cbVar.get()


class StartFrame(FilterFrame):
    def __init__(self, master, widgetRoot):
        super().__init__(master, widgetRoot, text="start amount", cmd=super()._cmd)


class CPUSecFrame(FilterFrame):
    def __init__(self, master, widgetRoot):
        super().__init__(
            master,
            widgetRoot,
            text="max cpu(/hr)",
            cmd=super()._cmd,
            entryDefault="0.1",
        )


class DurSecFrame(FilterFrame):
    def __init__(self, master, widgetRoot):
        super().__init__(
            master,
            widgetRoot,
            text="max dur(/hr)",
            cmd=self._cmd,
            entryDefault="0.02",
        )


class FeatureEntryFrame(FilterFrame):
    def __init__(self, master, widgetRoot):
        super().__init__(
            master,
            widgetRoot,
            text="feature",
            cmd=self._cmd,
            entryDefault="",
        )


class NumSummaryFrame:
    def __init__(self, master, *args, **kwargs):
        self.master = master
        self.w = ttk.Frame(*args, **kwargs)
        for col in range(6):
            self.w.columnconfigure(col, weight=1)
        self.w.rowconfigure(0, weight=1)
        self.w.rowconfigure(1, weight=1)
        widthDefault = 26

        rowlabel1 = ttk.Label(self.w, text="cpu", anchor="center", width=widthDefault)
        rowlabel2 = ttk.Label(self.w, text="dur")
        rowlabel3 = ttk.Label(self.w, text="start")
        rowlabel1.grid(row=1, column=0)
        rowlabel2.grid(row=2, column=0)
        rowlabel3.grid(row=3, column=0)

        self.headingMin = ttk.Label(self.w, text="min", width=widthDefault)
        self.heading20 = ttk.Label(self.w, text="~20%", width=widthDefault)
        self.heading40 = ttk.Label(self.w, text="~40%", width=widthDefault)
        self.heading60 = ttk.Label(self.w, text="~60%", width=widthDefault)
        self.heading80 = ttk.Label(self.w, text="~80%", width=widthDefault)
        self.headingMax = ttk.Label(self.w, text="max", width=widthDefault)

        for offset, heading in enumerate(
            [
                self.headingMin,
                self.heading20,
                self.heading40,
                self.heading60,
                self.heading80,
                self.headingMax,
            ]
        ):
            heading.grid(row=0, column=offset + 1)

        textDefault = "-"
        row1labels = []
        row2labels = []
        row3labels = []

        for _ in range(6):
            row1labels.append(ttk.Label(self.w, text=textDefault, width=widthDefault))
            row2labels.append(ttk.Label(self.w, text=textDefault, width=widthDefault))
            row3labels.append(ttk.Label(self.w, text=textDefault, width=widthDefault))

        for index, rowlabels in enumerate([row1labels, row2labels, row3labels]):
            for offset, cell in enumerate(rowlabels):
                cell.grid(row=index + 1, column=offset + 1, sticky="news")
        self.rows = (
            row1labels,
            row2labels,
            row3labels,
        )

    def clear(self):
        values_strlists = []
        for _ in range(3):
            values_strlists.append(["-", "-", "-", "-", "-", "-"])
        for row_offset, value_strlist in enumerate(values_strlists):
            for offset, cell in enumerate(self.rows[row_offset]):
                cell.configure(text=value_strlist[offset])

    def fill(self, values):
        # debug.dlog(pformat(values))
        # debug.dlog(pformat(values[1:-1]))
        values_strlists = []
        if values == None:
            self.clear()  # review
            debug.dlog("values none, cleared")
        else:
            for valuePath_list in [values.cpu, values.env, values.start]:
                temp_strlist = [
                    f"{value[0]} ({value[1]})" for value in valuePath_list[1:-1]
                ]
                temp_strlist.insert(0, str(valuePath_list[0]))
                temp_strlist.append(str(valuePath_list[-1]))
                values_strlists.append(temp_strlist)

        for row_offset, value_strlist in enumerate(values_strlists):
            for offset, cell in enumerate(self.rows[row_offset]):
                cell.configure(text=value_strlist[offset])
