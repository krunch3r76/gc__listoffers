import tkinter as tk
from tkinter import ttk

class CheckbuttonEntry(ttk.Frame):
    """A widget containing a checkbutton and entry together."""

    """dynamically assigned attributes
        .variable -> check_var
        .variable.widget -> CheckbuttonEntry object instance (owner of var)
            important to address .checkbutton, .entry internally/externally
        .variable.label_widget
        .variable.checkbutton_widget
        [ .error ] TODO


    """
    def __init__(
        self,
        parent, # eg the containing frame
        label, # the checkbutton label (string)
        check_var, # the boolean checkbox variable
        click_event, # the event to generate on click
        entry_var, # the variable reflecting the current input text
        entry_width, # how wide the entry is using average size of characters
        name='', # used to identify specific widget as in event emission
        focusout_event=None, # the event to generate on focusout (def to click_event)
        checkbutton_args=None, # configuration of checkbutton
        entry_args=None, # configuration of entry
        disable_var=None, # traced signal to disable
        debug_var=None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.name=name
        # self.columnconfigure(0, weight=1)
        # self.columnconfigure(1, weight=1)
        self.click_event = click_event
        focusout_event=focusout_event or click_event 

        # check button in frame
        check_button_frame = ttk.Frame(self, padding=(0,0,5,0))
        self.checkbutton=ttk.Checkbutton(check_button_frame)
        self.checkbutton.configure(text=label, variable=check_var, command=self.on_click)
        self.checkbutton.grid(row=0, column=0, sticky="w")
        # self.checkbutton.pack()

        #  self.checkbutton.state(['selected'])
        checkbutton_args = checkbutton_args or {}
        entry_args = entry_args or {}
        self.variable = check_var
        self.variable.widget = self

        # entry
        self.entry = ttk.Entry(self, textvariable=entry_var)
        self.entry.configure(width=entry_width)

        # self.variable.label_widget = self.entry
        # self.variable.checkbutton_widget = self.checkbutton


        # check_button_frame.grid(row=0, column=0, sticky="we")
        # self.entry.grid(row=0, column=1, sticky="we")

        check_button_frame.pack(
            side=tk.LEFT, expand=False, fill='x'
        )
        self.entry.pack(
            side=tk.LEFT, pady=3, ipady=5, expand=False, fill='x'
                )
        if disable_var != None:
            self.disable_var = disable_var
            self.disable_var.trace_add('write', self._check_disable)

        if debug_var != None:
            debug_var.trace_add('write', self._debug)


        self['padding']=(5,5,5,5)

        if self.variable.get() == False:
            self.entry.state(["disabled"])

        self.entry.bind('<FocusOut>', lambda e: self.entry.event_generate(focusout_event))

    def _check_disable(self, *_):
        # write traced to self._check_disable
        if not hasattr(self, 'disable_var'):
            return

        if self.disable_var.get():
            self.variable.widget.checkbutton.configure(state=tk.DISABLED)
            self.variable.widget.entry.configure(state=tk.DISABLED)
            # self.error.set('')
        else:
            self.variable.widget.checkbutton.configure(state=tk.NORMAL)
            self.variable.widget.entry.configure(state=tk.NORMAL)

    def on_click(self):
        # toggle entry
        # ...
        if self.variable.get() == True:
            self.variable.widget.entry.configure(state=tk.NORMAL)
        else:
            self.variable.widget.entry.configure(state=tk.DISABLED)
        self.event_generate(self.click_event)
        # print(type(self.variable.widget.entry.get()))

    def _debug(self, *_):
        # primarily for debugging visual placement
        self["borderwidth"] = 2
        self['relief']='solid'
