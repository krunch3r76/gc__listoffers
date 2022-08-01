import tkinter as tk
from tkinter import ttk

from checkbuttonentry import CheckbuttonEntry
from mycheckbutton import MyCheckbutton


class Console(tk.Text):
    def __init__(
            self,
            parent,
            disable_var=None,
            debug_var=None # not used yet
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

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.title("testing widgets")
            self.columnconfigure(0, weight=1)
            self.rowconfigure(0, weight=1)
            self.variables = Variables()
            variables = self.variables 
            self.bind("<<Clicked Max CPU>>", self.on_max_cpu_click)
            # disable_var.set(True)
            self.variables['debug_var'].set(True)

            self.console = Console(parent=self, height=7, width=40)
            self.console.grid(sticky="w")

            # <filters frame>
            filters = ttk.Frame(self)

            for c in range(5):
                filters.columnconfigure(c, weight=1)
            filters.grid(row=0, column=0, sticky="wes")

            CheckbuttonEntry(parent=filters, label="max cpu(/hr)", check_var=variables['filters']['max_cpu_checkVar'],
                             click_event="<<Clicked Max CPU>>", entry_var=variables['filters']['max_cpu_entryVar'],
                             entry_width=13, name="maxcpuFilter", disable_var=variables['disable_var'],
                             debug_var=variables['debug_var']
                             ).grid(row=0, column=0, sticky="e")

            CheckbuttonEntry(parent=filters, label="max dur(/hr)", check_var=variables['filters']['max_dur_checkVar'],
                             click_event="<<Clicked Max Duration>>", entry_var=variables['filters']['max_dur_entryVar'],
                             entry_width=13, name="maxdurFilter", disable_var=variables['disable_var'],
                             debug_var=variables['debug_var']
                             ).grid(row=0, column=1, sticky="we")

            CheckbuttonEntry(parent=filters, label="start amount", check_var=variables['filters']['start_checkVar'],
                             click_event="<<Clicked Start>>", entry_var=variables['filters']['start_entryVar'],
                             entry_width=13, name="startFilter", disable_var=variables['disable_var'],
                             debug_var=variables['debug_var']
                             ).grid(row=0, column=2, sticky="we")

            CheckbuttonEntry(parent=filters, label="feature", check_var=variables['filters']['feature_checkVar'],
                             click_event="<<clicked start>>", entry_var=variables['filters']['feature_entryVar'],
                             entry_width=13, name="featureFilter", disable_var=variables['disable_var'],
                             debug_var=variables['debug_var']
                             ).grid(row=0, column=3, sticky="we")

            MyCheckbutton(parent=filters, label="manual probe", check_var=variables['probe_checkVar'],
                            click_event="<<clicked probe>>", name="manualProbe", disable_var=variables['disable_var'],
                            debug_var=variables['debug_var']
                            ).grid(row=0, column=4, sticky="w")
            # </filters frame>

            self.console.write("who the what, the holy, whoa. your head's on fire")
    app = MiniApplication()
    app.mainloop()
