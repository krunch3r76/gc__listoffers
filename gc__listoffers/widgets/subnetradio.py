import tkinter as tk
from tkinter import ttk
import json
from .radiocombo import RadioCombo


class SubnetRadio(ttk.Frame):
    """
    .variable := the variable associated with the radiogroup (in: variable)
    .variable.widget := the SubnetRadio instance
    .variable.widget_combobox := the combobox (added in init)
    .variable.widget_combobox.variable := the variable linked to the selection (in: combo_var)
    """

    def __init__(
        self,
        parent,
        variable,  # varies according to selected state
        combo_var,  # whatever is selected in the combo box
        click_event,
        list_variable_json,  # StringVar with json string write traced to decode to update list
        name="",
        disable_var=None,
        debug_var=None,
        **kwargs
    ):

        super().__init__(parent, **kwargs)
        self.click_event = click_event
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        # self.list_variable = list()
        # if list_variable_json == None:
        #     list_variable_json = tk.StringVar(value="{}")
        self.list_variable_json = list_variable_json
        # self.list_variable_json.trace_add("write", self._update_list_variable)
        # self.rowconfigure(11, weight=1)
        ttk.Radiobutton(
            self,
            variable=variable,
            text="public",
            value="public",
            command=lambda: self.event_generate(self.click_event),
        ).grid(row=0, column=0, sticky="w", padx=25)

        RadioCombo(
            self,
            text="other",
            variable=variable,
            combo_var=combo_var,
            click_event=click_event,
            list_variable_json=list_variable_json,
            disable_var=disable_var,
        ).grid(row=1, column=0, sticky="w", padx=25)

        if debug_var != None:
            debug_var.trace_add("write", self._debug)
        # ttk.Radiobutton(
        #     self,
        #     variable=variable,
        #     text="other",
        #     value="other",
        #     command=lambda: self.event_generate(self.click_event),
        # ).grid(column=11, row=10, sticky="w")
        # combobox = ttk.Combobox(
        #     self,
        #     textvariable=combo_var,
        #     postcommand=self._update_list_variable,
        #     justify="left",
        # )
        # combobox.grid(column=12, row=10, sticky="we")

        self.variable = variable
        self.variable.widget = self
        # self.variable.widget_radiocombo =
        # self.variable.widget_combobox = combobox

        # combobox.variable = combo_var
        # combobox.variable.widget = self

    def _debug(self, *_):
        # primarily for debugging visual placement
        self["borderwidth"] = 2
        self["relief"] = "solid"

    def _debug_combobox_selected(self, e, *_):
        e.widget.selection_clear()
        e.widget.variable.widget.variable.set("other")
        # print(e.widget.variable.get())
        # print(e.widget.get())

    def _update_list_variable(self, *_):
        decoded_to_list = json.loads(self.list_variable_json.get())
        self.variable.widget_combobox[
            "values"
        ] = decoded_to_list  # self.list_variable = json(self.list_variable_json.get()).decode()
        # decode the json string in self.list_variable_json and set self.list_variable
