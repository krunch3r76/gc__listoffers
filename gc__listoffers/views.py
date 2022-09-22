import tkinter as tk
from tkinter import ttk
import json
from collections import namedtuple, UserList

from . widgets import CheckbuttonEntry
from . widgets import MyCheckbutton
from . widgets import MyButton
from . widgets import SubnetRadio
from . widgets import CountSummary
from . widgets import ProviderTree
from . widgets import Console

from debug import logger

RecordTuple = namedtuple('RecordTuple',
                            ['offerRowID', 'name', 'address', 'cpu_sec',
                             'duration_sec', 'fixed', 'cores', 'threads',
                             'version', 'most_recent_timestamp', 'modelname',
                             'freq', 'token_kind', 'features',
                             'featuresFiltered', 'mem_gib',
                             'storage_gib', 'json'
                             ])

class ProviderList(UserList):
    longestname = "name"

    
    def __init__(self, sequence=None):
        super().__init__(sequence)
        self._update_longest_name()

    def append(self, elem):
        self.data.append(elem)
        if len(elem.name) > len(self.longestname):
            self.longestname = elem.name

    def extend(self):
        raise "extend not supported"

    def _update_longest_name(self):
        for insertiontuple in self.data:
            if len(insertiontuple.name) > len(self.longestname):
                self.longestname = insertiontuple.name
        return len(self.longestname)

class ClassicView(tk.Frame):
    def clear_provider_tree(self):
        self.providerTree.remove_rows()

    def _on_providerlist_update(self, event):
        logger.debug("PROVIDER LIST UPDATED")
        # update relevant areas of the view
        # this may include reselecting previously selected (by address)
        # , updating the counts
        # , updating the stats

    def __init__frame110(self):
        frame110 = ttk.Frame(self)
        self.providerTree=ProviderTree(frame110, "<<ProviderRowSelected>>", debug_var=self.variables['debug_var'])
        self.providerTree.grid(row=100, column=100, sticky="news")
        frame110.columnconfigure(100, weight=1)
        frame110.rowconfigure(100,weight=1)

        return frame110

    def __init__frame130(self):
        variables = self.variables
        frame130 = ttk.Frame(self)
        for rc in range(100,104):
            frame130.columnconfigure(rc, weight=1)

        # <console>
        self.console = Console(parent=frame130, height=7, width=40)
        self.console.grid(row=100, column=100, sticky="wes", rowspan=2, padx=5)
        # </console>

        # <refresh button>
        MyButton(parent=frame130, label="Refresh", click_event="<<Clicked Refresh>>",
                 name='refreshButton', disable_var=variables['disable_var'],
                 debug_var=variables['debug_var']).grid(row=100, column=101, sticky="ws", padx=15)
        # </refresh button>

        # <update button>
        MyButton(parent=frame130, label="Apply", click_event="<<Clicked Update>>",
                 name='updateButton', disable_var=variables['disable_var'],
                 debug_var=variables['debug_var'], draw_disabled=True).grid(row=100, column=102, sticky="ws", padx=15)

        # MyButton(parent=refreshButtn

        # <subnet radios>
        SubnetRadio(parent=frame130, variable=variables['subnet_radioVar'],
                    click_event="<<Subnet Radio Pressed>>",
                    combo_var=variables['subnet_comboVar'],
                    list_variable_json=variables['subnet_list_json'],
                    name="subnetRadioGroup", disable_var=variables['disable_var'], debug_var=variables['debug_var'],
                    ).grid(row=101,column=101, sticky="news", padx=15)

        # </subnet radios>

        CountSummary(parent=frame130, totalCount=variables['counts']['totalNodes'],
                     glmNodeCount=variables['counts']['glmNodes'], tglmNodeCount=variables['counts']['tglmNodes'], 
                     name='counts', debug_var=variables['debug_var']
                     ).grid(row=101, column=102, sticky="news", padx=15)

        # <latest version checkbutton>
        MyCheckbutton(parent=frame130, label="latest version only", check_var=variables['latest_checkVar'],
                      click_event="<<Clicked Latest>>", name="latestVersion", disable_var=variables['disable_var'],
                      debug_var=variables['debug_var']
                      ).grid(row=100,column=103, sticky="news", padx=15)
        # </latest version checkbutton>
        return frame130

    def __init__frame140(self):
        variables = self.variables
        frame140 = ttk.Frame(self)
        frame140.rowconfigure(10, weight=1)
        frame140.grid(row=103, column=100, sticky="wse")
        for c in range(10,15):
            frame140.columnconfigure(c, weight=1)

        CheckbuttonEntry(parent=frame140, label="max cpu(/hr)", check_var=variables['filters']['max_cpu_checkVar'],
                         click_event="<<Clicked Max CPU>>", entry_var=variables['filters']['max_cpu_entryVar'],
                         entry_width=13, name="maxcpuFilter", disable_var=variables['disable_var'],
                         debug_var=variables['debug_var']
                         ).grid(row=10, column=10, sticky="we")

        CheckbuttonEntry(parent=frame140, label="max dur(/hr)", check_var=variables['filters']['max_dur_checkVar'],
                         click_event="<<Clicked Max Duration>>", entry_var=variables['filters']['max_dur_entryVar'],
                         entry_width=13, name="maxdurFilter", disable_var=variables['disable_var'],
                         debug_var=variables['debug_var']
                         ).grid(row=10, column=11, sticky="we")

        CheckbuttonEntry(parent=frame140, label="start amount", check_var=variables['filters']['start_checkVar'],
                         click_event="<<Clicked Start>>", entry_var=variables['filters']['start_entryVar'],
                         entry_width=13, name="startFilter", disable_var=variables['disable_var'],
                         debug_var=variables['debug_var']
                         ).grid(row=10, column=12, sticky="we")

        CheckbuttonEntry(parent=frame140, label="feature", check_var=variables['filters']['feature_checkVar'],
                         click_event="<<Clicked Feature>>", entry_var=variables['filters']['feature_entryVar'],
                         entry_width=13, name="featureFilter", disable_var=variables['disable_var'],
                         debug_var=variables['debug_var']
                         ).grid(row=10, column=13, sticky="we")

        MyCheckbutton(parent=frame140, label="manual probe", check_var=variables['probe_checkVar'],
                        click_event="<<Clicked Probe>>", name="manualProbe", disable_var=variables['disable_var'],
                        debug_var=variables['debug_var']
                        ).grid(row=10, column=14, sticky="w", padx=20)
        return frame140

        # </frame140 frame>

    def insert_provider_row(self, rowdict, last=False):
        self.providerTree.insert(rowdict, last)
        if rowdict != None:
            recordTuple = RecordTuple(**rowdict)
            self.providerlist.append(recordTuple)

    def __init__(self, parent, variables, model=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.providerlist = ProviderList()
        self.parent=parent
        self.model = model
        for rc in range(100,101):
            self.columnconfigure(rc, weight=1)
        self.variables = variables

        self.variables['debug_var'].set(True)

        frame110 = self.__init__frame110()
        frame110.grid(row=101, column=100, sticky="news")
        self.rowconfigure(101, weight=1)

        frame130 = self.__init__frame130()
        frame130.grid(row=102, column=100, sticky="ews")
        # self.rowconfigure(102, weight=1)

        frame140 = self.__init__frame140()
        frame140.grid(row=103, column=100, sticky="ews")
        # self.rowconfigure(103, weight=1)

        self.console.write("who the what, the holy, whoa. your head's on fire")
        alist=['a','b','c']
        variables['subnet_list_json'].set(json.dumps(alist))
        variables['debug_var'].set(True)

        parent.bind("<<Providerlist Updated>>", self._on_providerlist_update)
