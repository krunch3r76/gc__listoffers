import tkinter as tk
from tkinter import *
from tkinter import ttk
from .checkbuttonentry import CheckbuttonEntry

class ProbeFrame(CheckbuttonEntry):
    def __init__(self, parent):
        self.check_var = tk.BooleanVar(value=False)
        self.apikey_var = tk.StringVar(value="")
        super().__init__(
                parent=parent,
                label="manual probe",
                check_var=self.check_var,
                click_event="<<Clicked Manual Probe>>",
                entry_var=self.apikey_var,
                entry_width=38,
                name="probeWidget",
                focusout_event="<<OutFocused Manual Probe>>"
                )
        # self.manual_probe_cb = self.checkbutton
