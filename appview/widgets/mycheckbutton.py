import tkinter as tk
from tkinter import ttk

class MyCheckbutton(ttk.Checkbutton):
    def __init__(
            self,
            parent,
            label,
            check_var,
            click_event,
            name='',
            disable_var=None,
            debug_var=None,
            draw_disabled=False,
            **kwargs
            ):
        super().__init__(parent, **kwargs)
        self.name=name
        self.click_event = click_event
        self['text']=label
        self['variable']=check_var
        self['command']=self.on_click

        self.variable = check_var
        self.variable.widget = self

        if draw_disabled:
            self.variable.widget.configure(state=tk.DISABLED)

        if disable_var != None:
            self.disable_var = disable_var
            self.disable_var.trace_add('write', self._check_disable)

        if debug_var != None:
            debug_var.trace_add('write', self._debug)

    def on_click(self):
        # toggle entry
        # ...
        # if self.variable.get() == True:
        #     self.variable.widget.configure(state=tk.NORMAL)
        # else:
        #     self.variable.widget.configure(state=tk.DISABLED)

        self.event_generate(self.click_event)
        # print(type(self.variable.widget.entry.get()))

    def _debug(self, *_):
        # primarily for debugging visual placement
        try:
            self["borderwidth"] = 2
            self['relief']='solid'
        except:
            pass

    def _check_disable(self, *_):
        # write traced to self._check_disable
        if not hasattr(self, 'disable_var'):
            return

        if self.disable_var.get():
            self.variable.widget.configure(state=tk.DISABLED)
            # self.error.set('')
        else:
            self.variable.widget.configure(state=tk.NORMAL)
