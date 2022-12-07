import tkinter as tk
from tkinter import ttk

from .checkbuttonentry import CheckbuttonEntry
from .mycheckbutton import MyCheckbutton
from .mybutton import MyButton
from .subnetradio import SubnetRadio
from .countsummary import CountSummary
from .providertree import ProviderTree

class Console(tk.Text):
    def __init__(
            self,
            parent,
            disable_var=None,
            debug_var=None, # not used yet
            **kwargs
            ):
        super().__init__(parent, **kwargs)
        self.configure(state=tk.DISABLED)
        # https://stackoverflow.com/questions/54792599/how-can-i-make-a-tkinter-text-widget-unselectable 
        self.bindtags([str(self), str(parent), "all"])
        # self.bind('<FocusIn>', self._debug_event)

        self.configure(wrap="word")

        if disable_var != None:
            self.disable_var = disable_var
            self.disable_var.trace_add('write', self._check_disable)


    def _write(self, txt, length, current=0, time=25, newmsg=True):
        self["state"] = tk.NORMAL
        self.insert("end", txt[current])
        current += 1
        add_time = 0 # no delay unless the following
        if current != length:
            if txt[current - 1] == ".":
                add_time = time * 15
            elif txt[current - 1] == ",":
                add_time = time * 10
            # self["state"] = tk.DISABLED
            self.after(time + add_time, lambda: self._write( txt, length, current, time, newmsg))
            # self["state"] = "disabled"

    def write(self, msg):
        self["state"] = tk.NORMAL
        self.delete("1.0", "end")
        self._write(msg, len(msg))

    def _check_disable(self, *_):
        # write traced to self._check_disable
        if not hasattr(self, 'disable_var'):
            return

        if self.disable_var.get():
            self.variable.widget.configure(state=tk.DISABLED)
            # self.error.set('')
        else:
            self.variable.widget.configure(state=tk.NORMAL)

if __name__ == '__main__':
    # debugging
    import json
    from tkinter import *
    import sys
    from pathlib import Path
    sys.path.append(str(Path('..')))
    from models import Variables

    class MiniApplication(tk.Tk):
        """Application root window"""

        def on_max_cpu_click(self, event):
            # event.widget.variable determines whether off or on
            self.console.write("woo hoo, you activated the max cpu filter entry!")
            pass

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
            MyButton(parent=frame130, label="Update", click_event="<<Clicked Update>>",
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


        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            from pathlib import Path
            projectdir = Path(__file__).parent.parent.parent

            self.tk.call(
                "source", str(projectdir / "forest-ttk-theme/forest-light.tcl")
            )
            s=ttk.Style()
            s.theme_use("forest-light")


            self.title("testing widgets")
            for rc in range(100,101):
                self.columnconfigure(rc, weight=1)


            self.variables = Variables()
            variables = self.variables 
            self.bind("<<Clicked Max CPU>>", self.on_max_cpu_click)
            # disable_var.set(True)
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
    app = MiniApplication()
    app.mainloop()