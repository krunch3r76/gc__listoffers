# appview.py
import multiprocessing
from multiprocessing import Process, Queue
import itertools
from pprint import pprint, pformat  # debugging
import importlib
import sys
from collections import namedtuple
from pathlib import Path

yapapi_loader = importlib.util.find_spec("yapapi")
projectdir = Path(__file__).parent.parent

try:
    from tkinter import *
except ModuleNotFoundError:
    import sys

    print(
        "omigosh your python isn't linked with tcl.\nyou should install"
        " python that is. on ubuntu you could do this with its package manager"
        " by running the following command:"
    )
    print("$ \033[1msudo apt install python3-tk\033[0m")
    print("plese do this and run again!")
    sys.exit(1)
from tkinter import ttk
from tkinter import font

from datetime import datetime
import decimal
from decimal import Decimal
import json
import subprocess
import platform
import webbrowser

import debug
from .broca import fetch_new_dialog
from .tree import TreeFrame
from .selection_tree import SelectionTreeview
from .filterms_window import FiltermsWindow

if platform.system() == "Windows":
    import winsound


import os

from .frames import *

DIC411 = "#003366"
DIC544 = "#4D4D4D"


class TreeMenu(Menu):
    """
    contextual menu for the main tree (vs selection tree) view
    """

    def __init__(self, ctx, *Menu_args, **Menu_kwargs):
        """set up menu skeleton"""
        super().__init__(*Menu_args, **Menu_kwargs)
        self._ctx = ctx
        _ctx = self._ctx

        callbacks = {
            "show-raw": ctx._show_raw,
            "browse-stats": ctx.open_stats_page_under_cursor,
        }

        menu_items = [
            {"label": "<name>"},  # < > signifies a placeholder
            {"label": "view raw", "command": callbacks["show-raw"]},
            {
                "label": "browse to stats",
                "command": lambda: callbacks["browse-stats"](self.id_),
            },
            {"label": "exit menu", "command": self.grab_release},
        ]

        def add_command_for(label):
            self.add_command(
                **next(
                    (
                        menu_item
                        for menu_item in menu_items
                        if menu_item["label"] == label
                    )
                )
            )

        add_command_for("<name>")
        self.entryconfigure(0, state=DISABLED)
        self.add_separator()
        add_command_for("view raw")
        add_command_for("browse to stats")
        add_command_for("exit menu")

    def popup(self, name, event):
        """
        show the contextual menu
        :name: provider name to show at top
        in: name, event structure (for coordinates)
        post: _ctx.cursorOfferRowID, popup at absolute screen position
        """
        _ctx = self._ctx
        self.entryconfigure(0, label=name)
        self.post(event.x_root, event.y_root)  # absolute screen position

        self.id_ = _ctx.treeframe.tree.identify_row(event.y)  # widget relative


class SelTreeMenu(Menu):
    """
    contextual menu for the selection tree (vs main tree) view
    """

    def _add_addr_items(self, addr_text):
        """add a label to indicate which specific address is corresponding"""
        pass

    def __init__(self, ctx, *args, **kwargs):
        """set up menu skeleton
        in: ctx of AppView
        """
        super().__init__(*args, **kwargs)
        self.ctx = ctx
        label_to_callback = {
            "filterms": self.ctx._start_filterms_dialog,
            "exit menu": self.grab_release,
        }
        menu_items = [
            {"label": "filterms", "command": label_to_callback["filterms"]},
            {"label": "exit menu", "command": label_to_callback["exit menu"]},
        ]

        def add_command_for(label):
            self.add_command(
                **next(
                    (
                        menu_item
                        for menu_item in menu_items
                        if menu_item["label"] == label
                    )
                )
            )

        add_command_for("filterms")
        add_command_for("exit menu")

    def popup(self, event):
        """
        show the contextual menu
        in: event (for coordinated)
        post: contextual menu posted to absolute position of mouse click
        """
        self.post(event.x_root, event.y_root)  # absolute


class AppView:
    cancel_current_displayed_message = False  # review
    message_being_displayed = False  # review

    class Callbacks:
        def __init__(self, ctx):
            self.ctx = ctx

        def on_offer_text_selection(*args):
            self.ctx._on_offer_text_selection(args)

        def on_select():
            self.ctx.on_select()

        def on_none_selected():
            self.ctx.on_none_selected()

    #                       AppView __init__                           #


    def __init__(self):
        # icon

        self.refreshFrame = None
        # message queues used by controller to interface with this
        self.q_out = Queue()
        self.q_in = Queue()

        self.session_id = None  # timestamp of last refresh
        self.order_by_last = "'node.id'.name"  # current column to sort results
        # root Tk window and styling
        self.root = Tk()
        self.root.geometry("1256x768+100+200")
        s = ttk.Style()
        self.DARKMODE = (
            True if (datetime.now().hour > 19 or datetime.now().hour < 6) else False
        )

        if not self.DARKMODE:
            if sys.platform == "win32":
                self.root.tk.call(
                    "source",
                    str(projectdir / "Sun-Valley-ttk-theme/sun-valley.tcl"),
                )
                self.root.call("set_theme", "light")
            else:
                self.root.tk.call(
                    "source", str(projectdir / "forest-ttk-theme/forest-light.tcl")
                )
                s.theme_use("forest-light")
        else:
            if sys.platform == "win32":
                self.root.tk.call(
                    "source",
                    str(projectdir / "Sun-Valley-ttk-theme/sun-valley.tcl"),
                )
                self.root.call("set_theme", "dark")
            else:
                self.root.tk.call(
                    "source", str(projectdir / "forest-ttk-theme/forest-dark.tcl")
                )
                s.theme_use("forest-dark")
        import tkinter.font as tkfont
        default_font = tkfont.nametofont('TkDefaultFont')
        default_font.configure(family="DejaVu Sans", size=9)
        print(default_font.actual())

        current_datetime = datetime.now()
        root = self.root
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        root.rowconfigure(1, weight=0)
        root.rowconfigure(2, weight=0)
        root.rowconfigure(3, weight=0)

        self.fe_image_ico = PhotoImage(
            file=str(
                projectdir / "gs/"
                "the_empire_spaceship_and_sun_by_tempest790_db0ww24_48x48"
                ".png"
            )
        )
        self.root.iconphoto(True, self.fe_image_ico)

        # setup widgets and their linked variables
        self.subnet_var = StringVar()
        # self.other_entry_var = StringVar()
        # countlabel
        self.session_resultcount = 0  # number of rows currently on the table
        self.lastresultcount = 0  # temporary to store displayed
        # result number count before refresh
        self.cursorOfferRowID = None  # stores the RowID of a selected row
        decimal.getcontext().prec = 5  # sets the precision of displayed
        # decimal numbers
        self.rawwin = None  # a window for displaying raw results
        self.ssp = None  # current sound Process/Subprocess instance

        # configure layout
        style = ttk.Style()
        if self.DARKMODE == False:
            style.configure("Treeview.Heading", foreground=DIC411)

        root.title("Provider View")

        #################################################
        # numSummaryFrame                               #
        #################################################
        self.numSummaryFrame = NumSummaryFrame(self, root)
        self.numSummaryFrame.w.grid()

        #################################################
        # baseframe                                     #
        #################################################
        baseframe = ttk.Frame(root)
        baseframe.columnconfigure(0, weight=1)
        baseframe.columnconfigure(1, weight=1)
        baseframe.columnconfigure(2, weight=1)
        #        baseframe.columnconfigure(3, weight=1)
        baseframe.rowconfigure(0, weight=1)
        baseframe["padding"] = (0, 5, 0, 10)

        # baseframe--l_baseframe
        self.l_baseframe = ttk.Frame(baseframe)
        # self.l_baseframe.columnconfigure(0, weight=1)
        # self.l_baseframe.rowconfigure(0, weight=1)
        self.l_baseframe.grid(column=0, row=0, sticky="wns")
        self.l_baseframe["borderwidth"] = 2
        # self.l_baseframe['relief']='solid'

        # l_baseframe++console
        self.console = Text(self.l_baseframe, height=7, width=40)
        self.console["state"] = "disabled"
        self.console["wrap"] = "word"
        # self.console["borderwidth"] = 0

        # baseframe--refreshframe
        self.refreshFrame = RefreshFrame(
            self, self._toggle_refresh_controls_closure(), baseframe
        )
        self.refreshFrame.w["padding"] = (0, 0, 0, 0)
        self.refreshFrame.w.grid(column=1, row=0, sticky="wnes")
        self.refreshFrame.w["borderwidth"] = 2
        # self.refreshFrame.w["relief"] = "solid"

        # radioFrame
        self.radioFrame = RadioFrame(appView=self, refreshFrame=self.refreshFrame)
        self.radioFrame.w["padding"] = (0, 5, 0, 5)
        self.radioFrame.w.grid(column=0, columnspan=2, row=1, sticky=(W, N))

        self.cbv_lastversion = BooleanVar()
        self.cbv_lastversion.set(False)
        self.version_cb = ttk.Checkbutton(
            self.refreshFrame.w,
            text="latest version only",
            padding=(10, 0, 10, 0),
            variable=self.cbv_lastversion,
            command=lambda: self._update_cmd({"cmd": "check version"}),
        )
        self.version_cb.grid(row=0, column=2, sticky="w")

        # baseframe--count_frame
        self.count_frame = CountFrame(self, baseframe)
        self.count_frame.w.grid(column=2, row=0, sticky="")

        # self.l_baseframe['borderwidth']=2
        # self.l_baseframe['relief']='solid'

        self.console.grid(row=0, column=0, sticky="nwes")

        baseframe.grid(column=0, row=2, sticky="nwes")
        # /baseframe

        #################################################
        # subbaseframe                                  #
        #################################################
        subbaseframe = ttk.Frame(root)
        subbaseframe.rowconfigure(0, weight=0)
        subbaseframe.columnconfigure(0, weight=1)
        subbaseframe.columnconfigure(1, weight=1)
        subbaseframe.columnconfigure(2, weight=1)

        self.__count_selected = StringVar()
        # subbaseframe++label_selectioncount
        select_count_frame = ttk.Frame(subbaseframe)

        self.label_selectioncount = ttk.Label(
            subbaseframe, textvariable=self.__count_selected
        )
        self.label_selectioncount["foreground"] = "#217346"
        self.label_selectioncount.grid(row=0, column=0, sticky="wnes")
        # self.label_selectioncount.grid_forget()
        select_count_frame["borderwidth"] = 2
        # select_count_frame['relief']='ridge'
        # select_count_frame.grid(row=0, column=0, sticky="wnes")

        filterframe = ttk.Frame(subbaseframe)
        filterframe.columnconfigure(0, weight=1)
        filterframe.columnconfigure(1, weight=1)
        filterframe.columnconfigure(2, weight=1)
        # subbaseframe++cpusec_entryframe
        # self.cpusec_entryframe = CPUSecFrame(self, filterframe)
        # self.cpusec_entryframe.w.grid(column=0, row=0, sticky="e")
        self.cpusec_entryframe = CPUSecFrame(self, filterframe)
        self.cpusec_entryframe.grid(column=0, row=0, sticky="w", padx=10)
        # subbaseframe++dursec_entryframe
        self.dursec_entryframe = DurSecFrame(self, filterframe)
        self.dursec_entryframe.grid(column=1, row=0, sticky="w", padx=10)
        # subbaseframe++start_entryframe
        self.start_entryframe = StartFrame(self, filterframe)
        self.start_entryframe.grid(column=2, row=0, sticky="w", padx=10)
        # subbaseframe++feature_entryframe
        self.feature_entryframe = FeatureEntryFrame(self, filterframe)
        self.feature_entryframe.grid(column=3, row=0, sticky="e", padx=10)

        filterframe["borderwidth"] = 2
        # filterframe['relief']='ridge'
        filterframe.grid(row=0, column=1, sticky="wnes")
        # //filterframe

        # subbaseframe++stub
        stubframe = ttk.Frame(subbaseframe)
        stub = ttk.Label(stubframe)
        stub.grid(row=0, column=2, sticky="wnes")
        # stubframe.grid(row=0,column=2, sticky="wnes")
        stubframe["borderwidth"] = 2
        # stubframe['relief']='ridge'

        subbaseframe["borderwidth"] = 2
        # subbaseframe['relief']='ridge'
        self.cbv_manual_probe = BooleanVar()
        self.manual_probe_cb = ttk.Checkbutton(
            subbaseframe,
            text="manual probe",
            padding=(0, 0, 50, 0),
            variable=self.cbv_manual_probe,
        )
        if yapapi_loader == None:
            self.manual_probe_cb["state"] = "disabled"
        self.manual_probe_cb.grid(row=0, column=4, sticky="")
        subbaseframe.grid(row=3, column=0, sticky="we")
        # /subbaseframe

        #################################################
        # treeframe                                     #
        #################################################
        self.treeframe = TreeFrame(self, root)
        treeframe = self.treeframe
        treeframe.columnconfigure(0, weight=1)
        treeframe.columnconfigure(1, weight=0)
        treeframe.rowconfigure(0, weight=1)  # resize by same factor as
        # root height
        treeframe.columnconfigure(2, weight=0)
        treeframe["padding"] = (0, 0, 0, 10)

        # treeframe--tree
        self.treeframe.tree.configure(padding=(0, 0, 0, 15))
        # treeframe--selection_tree
        self.selection_tree = SelectionTreeview(self, treeframe)

        self.selection_tree.pseudogrid(column=2, row=0, sticky="nwes")
        treeframe.grid(column=0, row=0, sticky="news")
        # /treeframe

        self.subnet_var.set("public-beta")

        root.bind("<Escape>", self.on_escape_event)

        self._rewrite_to_console(fetch_new_dialog(0))

        self.filtermswin = None
        self._states = dict()
        self.whetherUpdating = False

    #                           __call__                                     <
    def __call__(self):
        root = self.root

        self._build_menus()

        # root.bind('<ButtonRelease-3>', do_popup )
        # TODO move to __init__
        if root.tk.call("tk", "windowingsystem") == "aqua":
            root.bind("<2>", self.do_popup)
            root.bind("<Control-1>", self.do_popup)
        else:
            root.bind("<3>", self.do_popup)

        root.mainloop()

    #                           __call__                                     >

    @property
    def cursorOfferRowID(self):
        return self.__cursorOfferRowID

    @cursorOfferRowID.setter
    def cursorOfferRowID(self, val):
        # debug.dlog(f"setter: setting cursorOfferRowID to {val}")
        self.__cursorOfferRowID = val

    @property
    def count_selected(self):
        return self.__count_selected.get()

    @count_selected.setter
    def count_selected(self, newcount):
        self.__count_selected.set(newcount)
        if newcount > 1:
            self.label_selectioncount.grid(column=0, row=0, sticky="w")
        else:
            self.label_selectioncount.grid_remove()

    #                       add_text_over_time                               #
    def add_text_over_time(self, text, txt, length, current=0, time=25, newmsg=True):
        """add text character by character to console"""
        text["state"] = "normal"
        if txt == "":
            text.delete("1.0", "end")
            return

        if newmsg:
            text.delete("1.0", "end")
            newmsg = False
        text.insert("end", txt[current])
        current += 1
        add_time = 0
        if current != length:
            if txt[current - 1] == ".":
                add_time = time * 15
            elif txt[current - 1] == ",":
                add_time = time * 10
            text["state"] = "disabled"
            self.root.after(
                time + add_time,
                lambda: self.add_text_over_time(
                    text, txt, length, current, time, newmsg
                ),
            )

        text["state"] = "disabled"

    #                       _rewrite_to_console                              #
    def _rewrite_to_console(self, msg):
        """clear the console label and write a new message"""
        self.console.grid_remove()
        self.console = Text(self.l_baseframe, height=7, width=40)
        self.console["state"] = "disabled"
        self.console["wrap"] = "word"
        self.console["borderwidth"] = 0
        self.console.grid(row=0, column=0, sticky="nwes")

        if msg:
            self.add_text_over_time(self.console, msg, len(msg))
        else:
            self.add_text_over_time(self.console, "", 0)

    #                       _stateRefreshing                                 #
    def _stateRefreshing(self, b=None):
        if b == True:
            self._states["refreshing"] = True
        elif b == False:
            self._states["refreshing"] = False
        elif b == None:
            return self._states.get("refreshing", False)

    #                       _update                                          #
    def _update(self, results, refresh=True):
        """update gui with the input results
        called by: handle_incoming_result
        """
        if refresh:
            self.session_resultcount = len(results)
        self.treeframe._update_headings()
        self.treeframe.notify_insert_begin()
        for result in results:
            result = list(result)
            currency_unit = result[13].split("-")[-1]
            # one of { 'tglm', 'glm' }
            ResultsNT = namedtuple(
                "resultsNT",
                [
                    "offerRowID",
                    "name",
                    "address",
                    "cpu_sec",
                    "duration_sec",
                    "fixed",
                    "cores",
                    "threads",
                    "version",
                    "max_timestamp",
                    "maxversion",
                    "modelname",
                    "modelfreq",
                    "platform_kind",
                    "filtered_features",
                    "mem",
                    "storage",
                ],
            )
            resultsNT = ResultsNT(*result)

            self.treeframe.insert(
                "",
                "end",
                values=(
                    resultsNT.offerRowID,  # 0
                    resultsNT.name,  # 1
                    resultsNT.address,  # 2
                    Decimal(resultsNT.cpu_sec) * Decimal(3600.0),  # 3
                    Decimal(resultsNT.duration_sec) * Decimal(3600.0),  # 4
                    resultsNT.fixed,  # 5 # TODO MAKE DECIMAL
                    resultsNT.cores,  # 6
                    resultsNT.threads,  # 7
                    resultsNT.version,  # 8
                    resultsNT.modelname,  # result[11], #9
                    resultsNT.filtered_features,  # result[14], #10
                    resultsNT.mem,  # 11
                    resultsNT.storage,  # 12
                    resultsNT.modelfreq,  # 13
                ),
                currency_unit=currency_unit,
            )
        self.treeframe.notify_insert_end()
        current_resultcount = len(results)
        # query tree for glm and tglm counts

        glmcounts = self.treeframe.glmcounts(
            reverse=False if self.subnet_var.get() == "public-beta" else True
        )

        self.count_frame.update_counts(str(current_resultcount), *glmcounts, "")
        # self.count_frame.resultcount_var.set(str(current_resultcount))
        # debug.dlog(pformat(self.tree.numerical_summary(False if self.subnet_var.get() =='public-beta' else True)))
        self.numSummaryFrame.fill(
            self.treeframe.numerical_summary(
                False if self.subnet_var.get() == "public-beta" else True
            )
        )

        if not refresh:
            disp = ""
            if (
                self.lastresultcount != 0
                and self.session_resultcount != current_resultcount
            ):
                disp += "/" + str(self.session_resultcount) + "("
                diff = current_resultcount - self.lastresultcount
                POS = False
                if diff > 0:
                    disp += "+"
                disp += str(current_resultcount - self.lastresultcount) + ")"
                # self.resultdiffcount_var.set(disp)
            else:
                pass
            # self.resultdiffcount_var.set("")  # consider edge cases

        if refresh:
            self.refreshFrame._toggle_refresh_controls()

        self._stateRefreshing(False)
        self.whetherUpdating = False

        if refresh:
            self._rewrite_to_console(fetch_new_dialog(3))
        else:
            self._rewrite_to_console(None)

        selected_addresses = self.treeframe.last_cleared_selection
        matched_prev_selections = []
        if not refresh and len(selected_addresses) > 0:
            selected_rowids = [
                selected_address[0] for selected_address in selected_addresses
            ]
            for rowitem in self.treeframe.tree.get_children(""):
                cursor_rowid = self.treeframe.tree.item(rowitem)["values"][0]
                if cursor_rowid in selected_rowids:
                    matched_prev_selections.append(rowitem)

        if len(matched_prev_selections) > 0:
            self.treeframe.tree.selection_set(*matched_prev_selections)
        else:
            self.treeframe.last_cleared_selection.clear()
            self.treeframe.on_select()
            # self.on_none_selected()

    #                           _refresh_cmd                                 <
    def _refresh_cmd(self, *args):
        """create a new session and query model before handing off
        control to self.handle_incoming_result"""
        self._stateRefreshing(True)
        self.cursorOfferRowID = None

        # describe what's happening to client in console area
        if not self.cbv_manual_probe.get():
            self._rewrite_to_console(fetch_new_dialog(1))
        else:
            self._rewrite_to_console(fetch_new_dialog(9))
        # disable controls
        self.refreshFrame._toggle_refresh_controls()

        # reset widgets to be refreshed
        # self.count_frame.resultcount_var.set("")
        self.numSummaryFrame.clear()
        self.count_frame.clear_counts()
        # self.resultdiffcount_var.set("")
        self.treeframe.clearit()
        # self.tree.delete(*self.tree.get_children())
        self.treeframe.tree.update_idletasks()

        # build sql statement
        ss = self._update_or_refresh_sql()

        # create new session id (current time)
        self.session_id = str(datetime.now().timestamp())

        # ask controller to query model for results
        msg_out = {
            "id": self.session_id,
            "msg": {
                "subnet-tag": self.subnet_var.get(),
                "sql": ss,
                "manual-probe": self.cbv_manual_probe.get(),
            },
        }
        self.q_out.put_nowait(msg_out)

        # wait on reply
        self.root.after(5, self.handle_incoming_result)

    #                       _refresh_cmd                                     >

    #                       _toggle_refresh_constrols_closure                <
    def _toggle_refresh_controls_closure(self):
        disabled = False
        other_entry_was_enabled = False
        # maxcpu_was_enabled = False
        # maxdur_was_enabled = False

        def toggle():
            nonlocal disabled
            nonlocal other_entry_was_enabled
            radio_frame = self.radioFrame
            refreshFrame = self.refreshFrame
            if not disabled:
                refreshFrame.refreshButton.state(["disabled"])
                refreshFrame.updateButton.state(["disabled"])
                radio_frame.publicbeta_rb.state(["disabled"])
                radio_frame.publicdevnet_rb.state(["disabled"])
                if radio_frame.other_entry.instate(["!disabled"]):
                    other_entry_was_enabled = True
                radio_frame.other_rb.state(["disabled"])
                radio_frame.other_entry.state(["disabled"])

                self.cpusec_entryframe.disable()
                self.dursec_entryframe.disable()
                self.start_entryframe.disable()
                self.feature_entryframe.disable()
                self.version_cb.state(["disabled"])
                self.manual_probe_cb["state"] = "disabled"
                disabled = True
            else:
                refreshFrame.refreshButton.state(["!disabled"])
                refreshFrame.updateButton.state(["!disabled"])
                radio_frame.publicbeta_rb.state(["!disabled"])
                radio_frame.publicdevnet_rb.state(["!disabled"])
                radio_frame.other_rb.state(["!disabled"])
                if other_entry_was_enabled:
                    radio_frame.other_entry.state(["!disabled"])

                self.cpusec_entryframe.enable()
                self.dursec_entryframe.enable()
                self.start_entryframe.enable()
                self.feature_entryframe.enable()
                self.version_cb.state(["!disabled"])

                if yapapi_loader != None:
                    self.manual_probe_cb["state"] = "!disabled"

                disabled = False

        return toggle

    #                       _toggle_refresh_constrols_closure                >

    #                               _update_cmd                              <
    def _update_cmd(self, more_d=None):
        """query model for rows on current session_id before handing off
        control to self.handle_incoming_result"""
        """more_d is an optional dictionary with additonal instructions
        tied to specific keys, so far 'sort_on'"""
        if more_d == None:
            more_d = dict()
        if more_d.get("cmd", None) == "check version":
            print(f"Checking version {self.cbv_lastversion.get()}")
            self.treeframe.change_visibility(
                self.treeframe.Field.version, not self.cbv_lastversion.get()
            )
            self.treeframe._update_headings()

        if not self.session_id:
            return

        self.whetherUpdating = True
        if self.cursorOfferRowID == None:
            self.cursorOfferRowID = self.treeframe.get_selected_rowid()

        self._stateRefreshing(True)

        # self.refreshFrame._toggle_refresh_controls()

        if self.count_frame.resultcount_var.get() != "":
            self.lastresultcount = int(self.count_frame.resultcount_var.get())
        else:
            self.lastresultcount = 0

        # self.count_frame.resultcount_var.set("")
        # self.resultdiffcount_var.set("")
        self.count_frame.clear_counts()
        self.numSummaryFrame.clear()
        self.treeframe.clearit(retain_selection=True)

        if not self.cbv_lastversion.get():
            self.treeframe.change_visibility(TreeFrame.Field.version, True)
        else:
            self.treeframe.change_visibility(TreeFrame.Field.version, False)
        self.treeframe._update_headings()
        # if len(args) > 0 and 'sort_on' in args[0]:
        if more_d and "sort_on" in more_d:
            if more_d["sort_on"] != "all":
                self.order_by_last = more_d["sort_on"]  # extract header
                # name to sort_on stored in value of key
            else:
                debug.dlog(more_d)
                self.order_by_last = None
        ss = self._update_or_refresh_sql()

        # TODO remove subnet-tag, it is already associated with the id
        msg = {"subnet-tag": self.subnet_var.get(), "sql": ss}
        self._send_message_to_model(msg)

        results = None
        msg_in = None
        self.handle_incoming_result(refresh=False)

    #                               _update_cmd                              >

    #                   _update_or_refresh_sql                               <
    # called from  _update_cmd, _refresh_cmd
    def _update_or_refresh_sql(self):
        """build a sql select statement when either update or refreshing
        and return text"""
        feature_filter = ""
        if self.feature_entryframe.whether_checked:
            feature_filter = self.feature_entryframe.entryVar.get()
        ss = """
select 'node.id'.offerRowID
, 'node.id'.name
, 'offers'.address
, 'com.pricing.model.linear.coeffs'.cpu_sec
, 'com.pricing.model.linear.coeffs'.duration_sec
, 'com.pricing.model.linear.coeffs'.fixed
, 'inf.cpu'.cores
, 'inf.cpu'.threads
, 'runtime'.version
, MAX('offers'.ts)
, (select 'runtime'.version FROM 'runtime'
    ORDER BY 'runtime'.version DESC LIMIT 1) AS mv
, 'inf.cpu'.brand AS modelname
, (SELECT grep_freq('inf.cpu'.brand)
) AS freq
, 'com.payment.platform'.kind
        """

        ss += f""",(
                SELECT json_group_array(value) FROM
                ( SELECT value FROM json_each('inf.cpu'.[capabilities])
                WHERE json_each.value LIKE '%{feature_filter}%' )
                ) AS filteredFeatures
        """

        ss += f"""
, ROUND('inf.mem'.gib,2)
, ROUND('inf.storage'.gib,2)
"""
        ss = (
            ss + " FROM 'node.id'"
            " JOIN 'offers' USING (offerRowID)"
            " JOIN 'com.pricing.model.linear.coeffs' USING (offerRowID)"
            " JOIN 'runtime'  USING (offerRowID)"
            " JOIN 'inf.cpu' USING (offerRowID)"
            " JOIN 'com.payment.platform' USING (offerRowID)"
            " JOIN 'inf.mem' USING (offerRowID)"
            " JOIN 'inf.storage' USING (offerRowID)"
            " WHERE 'runtime'.name = 'vm'"
        )

        if self.cbv_lastversion.get():
            ss += " AND 'runtime'.version = mv"

        epsilon = "0.000000001"

        def from_secs(decstr):
            epsilonized = Decimal(decstr) / Decimal("3600.0")
            return epsilonized

        if (
            self.cpusec_entryframe.whether_checked
            and self.cpusec_entryframe.entryVar.get()
        ):
            cpu_per_sec = from_secs(self.cpusec_entryframe.entryVar.get())
            ss += (
                f" AND 'com.pricing.model.linear.coeffs'.cpu_sec - {cpu_per_sec}"
                f" <=  {epsilon}"
            )
            # ss += f" AND ('com.pricing.model.linear.coeffs'.cpu_sec - {cpu_per_sec}) > 0.00001"
            # ss += f" AND 'com.pricing.model.linear.coeffs'.cpu_sec <= " f"'{cpu_per_sec}'"

        if (
            self.dursec_entryframe.whether_checked
            and self.dursec_entryframe.entryVar.get()
        ):
            duration_per_sec = from_secs(self.dursec_entryframe.entryVar.get())
            ss += (
                f" AND 'com.pricing.model.linear.coeffs'.duration_sec "
                f" - {duration_per_sec} < {epsilon}"
            )

        if (
            self.start_entryframe.whether_checked
            and self.start_entryframe.entryVar.get()
        ):
            start_fee_max = float(self.start_entryframe.entryVar.get())
            ss += f" AND 'com.pricing.model.linear.coeffs'.fixed <= {start_fee_max}"

        if (
            self.feature_entryframe.whether_checked
            and self.feature_entryframe.entryVar.get()
        ):
            ss += ""
            ss += f"""
                 AND json_array_length(filteredFeatures) > 0
                """

        if self.order_by_last:
            ss += " GROUP BY 'offers'.address"
            ss += f" ORDER BY {self.order_by_last}"
            ss += " COLLATE NOCASE"
            pass
        else:
            path_tuple = self.treeframe._model_sequence_from_headings()
            ss += " GROUP BY 'offers'.address"
            ss += " ORDER BY "
            for i in range(len(path_tuple) - 1):
                ss += f"{path_tuple[i]}, "
            ss += f"{path_tuple[len(path_tuple)-1]}"
            ss += " COLLATE NOCASE"

        debug.dlog(ss)

        return ss

    #                   _update_or_refresh_sql                               >

    #                               on_escape_event                          <
    def on_escape_event(self, e):
        mapped = list(
            filter(
                lambda menu: menu.winfo_ismapped() == 1, [self.menu, self.seltree_menu]
            )
        )
        if len(mapped) > 0:
            for menu in mapped:
                menu.grab_release()
                menu.unpost()
        else:
            self.root.destroy()

    #                               on_escape_event                          <

    #                       _on_offer_text_selection                         <
    def _on_offer_text_selection(self, *args):
        e = args[0]
        selection_range = e.widget.tag_ranges("sel")
        if selection_range:
            selection = e.widget.get(*selection_range)
            self.root.clipboard_clear()
            self.root.clipboard_append(selection)

    #                       _on_offer_text_selection                         >

    #                   _on_other_radio                                      <
    def _on_other_radio(self, *args):
        self.radioFrame.other_entry.state(["!disabled"])
        # debug.dlog(self.other_entry_var.get() )
        self.radioFrame.other_rb["value"] = self.radioFrame.other_entry_var.get()
        self.subnet_var.set(self.radioFrame.other_entry_var.get())

    #                   _on_other_radio                                      >

    #                       on_select                                        <
    def on_select(self):
        """update selectionList tree with the current selection
        called by tree.on_select"""
        self.selection_tree.update(self.treeframe.list_selection_addresses())
        self.selection_tree.regrid()

    #                       on_select                                        >

    #                       on_none_selected                                 <
    def on_none_selected(self):
        """remove the selected list from the view
        called by tree.on_select
        """
        self.selection_tree.clearit()
        self.selection_tree.degrid()
        self.treeframe.last_cleared_selection.clear()

    #                       on_none_selected                                 >

    #                           _show_raw                                    <
    def _show_raw(self, *args):
        ss = f"select json from extra WHERE offerRowID " f"= {self.cursorOfferRowID}"
        # review the need to pass subnet-tag on update TODO
        self.q_out.put_nowait(
            {
                "id": self.session_id,
                "msg": {"subnet-tag": self.subnet_var.get(), "sql": ss},
            }
        )

        results = None
        msg_in = None
        self.root.after(10, lambda: self.handle_incoming_result_extra())

    #                           _show_raw                                    >

    #                       open_stats_page_under_cursor                     <
    def open_stats_page_under_cursor(self, node_address):
        """
        pre:
        """
        debug.dlog(node_address)
        url = f"https://stats.golem.network/network/provider/{node_address}"
        webbrowser.open_new(url)

    #                       open_stats_page_under_cursor                     >

    #                       _send_message_to_model                           <
    def _send_message_to_model(self, msg):
        """creates a message containing the session id and the input
        msg and places it into the queue out to the model"""
        d = {"id": self.session_id, "msg": msg}
        self.q_out.put_nowait(d)

    #                       _send_message_to_model                           >

    #                       handle_incoming_result                           <
    def handle_incoming_result(self, refresh=True):
        """wait for results from model before passing control over to
        self._update"""
        path_to_sound_file = Path(projectdir / "gs/transformers.wav")

        def __play_sound(self):
            if platform.system() == "Windows":
                self.ssp = Process(
                    target=winsound.PlaySound,
                    # args=(".\\gs\\transformers.wav", winsound.SND_FILENAME),
                    args=(str(path_to_sound_file), winsound.SND_FILENAME),
                    daemon=True,
                )
                self.ssp.start()
            elif platform.system() == "Linux":
                self.ssp = subprocess.Popen(
                    ["aplay", str(path_to_sound_file)],
                    # ["aplay", "gs/transformers.wav"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif platform.system() == "Darwin":
                self.ssp = subprocess.Popen(
                    ["afplay", str(path_to_sound_file)],
                    # ["afplay", "gs/transformers.wav"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

        def __on_error(self, results):
            debug.dlog(f"error results: {results}")
            if results[1] == "invalid api key":
                self._rewrite_to_console(fetch_new_dialog(4))
            elif results[1] == "invalid api key server side":
                self._rewrite_to_console(fetch_new_dialog(6))
            elif results[1] == "connection refused":
                self._rewrite_to_console(fetch_new_dialog(7))
            elif results[1] == "cannot connect to yagna":
                self._rewrite_to_console(fetch_new_dialog(8))
            else:
                self._rewrite_to_console(fetch_new_dialog(5))
            if refresh:
                self.refreshFrame._toggle_refresh_controls()
            # may need to call _update with 0 results...

        try:
            msg_in = self.q_in.get_nowait()
        except multiprocessing.queues.Empty:
            # msg_in = None
            if refresh:
                if self.ssp == None:
                    if self.cbv_manual_probe.get():
                        __play_sound(self)
                elif self.ssp != None:
                    if isinstance(self.ssp, subprocess.Popen):
                        try:
                            self.ssp.wait(0.01)
                        except:
                            pass
                        else:
                            self.ssp = None
                    else:  # Process
                        if not self.ssp.is_alive():
                            self.ssp = None

            self.root.after(2, lambda: self.handle_incoming_result(refresh))
        else:
            results = msg_in["msg"]

            if len(results) > 1 and results[0] == "error":
                __on_error(self, results)
            else:
                debug.dlog(f"first of model results: {results[0]}\n", 10)
                self._update(results, refresh)
                # toggle_refresh_controls down the line

    #                       handle_incoming_result                           >

    #                       handle_incoming_result_extra                     <
    def handle_incoming_result_extra(self):
        # wait on a response from the model then extract the raw props (extra)
        try:
            msg_in = self.q_in.get_nowait()
        except multiprocessing.queues.Empty:
            msg_in = None
            self.root.after(10, lambda: self.handle_incoming_result_extra())
        else:
            results = msg_in["msg"]

            results_json = json.loads(results[0][0])
            props = results_json  # full results including props
            props_s = json.dumps(props, indent=5)
            # create/replace a new window
            self.rawwin = Toplevel(self.root)
            self.rawwin.columnconfigure(0, weight=1)
            self.rawwin.rowconfigure(0, weight=1)
            self.rawwin.title(props["props"]["golem.node.id.name"])
            f = ttk.Frame(self.rawwin)
            f.grid(column=0, row=0, sticky="news")
            f.columnconfigure(0, weight=1)
            f.rowconfigure(0, weight=1)
            txt = Text(f)
            txt.grid(column=0, row=0, sticky="news")
            txt.insert("1.0", props_s)
            txt.configure(state="disabled")
            txt.bind("<<Selection>>", self._on_offer_text_selection)

    #                       handle_incoming_result_extra                     >

    # TODO abstract and consolidate common code
    #                           _cb_feature_checkbutton                      <
    def _cb_feature_checkbutton(self):
        if self.feature_entryframe.cbFeatureEntryVar.get() == "feature":
            self.feature_entryframe.feature_entry.state(["!disabled"])
        else:
            self.feature_entryframe.feature_entry.state(["disabled"])
            self._update_cmd()

    #                           _cb_feature_checkbutton                      >

    #                           do_popup                                     <
    def do_popup(self, event):
        try:
            # identify the coordinates of tree
            # print(tree.state())
            if self.treeframe.tree.instate(["!hover"]) and self.selection_tree.instate(
                ["!hover"]
            ):
                return

            if (
                self.treeframe.tree.instate(["hover"])
                and self.treeframe.tree.identify_region(event.x, event.y) == "cell"
            ):
                id_ = self.treeframe.tree.identify_row(event.y)
                self.menu.popup(
                    self.treeframe.tree.item(self.treeframe.tree.identify_row(event.y))[
                        "values"
                    ][1],
                    event,
                )

                # update context of what row corresponded to the context
                # menu click
                self.cursorOfferRowID = self.treeframe.tree.item(
                    self.treeframe.tree.identify_row(event.y)
                )["values"][0]

            elif self.selection_tree.instate(["hover"]):
                self.seltree_menu.popup(event)

        except IndexError:
            debug.dlog("index error")
            pass
        finally:
            # todo, ensure grab_set called
            self.menu.grab_release()

    #                           do_popup                                     >

    #                           _start_filterms_dialog                       <
    def _start_filterms_dialog(self):
        """
        pre: selection_tree has at least 1 row, grab_set must be
        called on the dialog window
        """
        self.filtermswin = FiltermsWindow()  # pre: grab_set is called
        # on filtermswindow on init

        if self.filtermswin:
            pass
            self.filtermswin.set_content(self.selection_tree.get_rows())
        self.filtermswin.grab_release()

    #                           _start_filterms_dialog                       >

    #                           _build_menus                                 <
    def _build_menus(self):
        """build (popup) menu skeletons and store in self context
        post: self.menu, self.seltree_menu
        called by: __call__()
        """
        root = self.root
        root.option_add("*tearOff", FALSE)

        # popup menu for main tree row item
        self.menu = TreeMenu(self)

        # popup menu for selection tree (any area)
        self.seltree_menu = SelTreeMenu(self)

    #                           _build_menus                                 >
