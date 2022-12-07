import tkinter as tk
from tkinter import ttk
import json

# stickies
# combobox.bind("<<ComboboxSelected>>", self._debug_combobox_selected)


class RadioCombo(ttk.Frame):
    # implement a frame that provides a radio button associated with a combobox
    """
    _list_variable_json := externally updated list of subnets

    _update_list_variable() := refreshes combobox list given state of _list_variable_json
    """

    def __init__(
        self,
        parent,
        text,  # text of the radiobutton e.g. "other"
        variable,  # radiogroup's value when radiobutton is selected (e.g. text)
        combo_var,  # assigned the text/selection in the combobox
        click_event,  # radio group's click event
        list_variable_json,  # dynamic list of subnets from external source
        name="",  # not used
        disable_var=None,
        debug_var=None,
        **kwargs
    ):
        super().__init__(parent)
        ttk.Radiobutton(
            self,
            variable=variable,
            text=text,
            value=text,  # written to variable
            command=lambda: self.event_generate(click_event),
        ).grid(row=0, column=0)

        # self.list_variable_json.trace_add("write", self._update_list_variable) # parse variable contents upon change
        # commented because update not always appropriate (e.g. only when interacting with the combobox) <<ComboboxSelected>>
        combobox = ttk.Combobox(
            self,
            textvariable=combo_var,
            postcommand=self._update_list_variable,  # get the current listings on init
        ).grid(row=0, column=1)

    def _update_list_variable(self):
        # parses contents of list_variable_json to update the combobox listed values
        pass
