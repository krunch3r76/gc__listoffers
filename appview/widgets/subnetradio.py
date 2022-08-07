
import tkinter as tk
from tkinter import ttk
import json

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
            variable, # varies according to selected state
            combo_var, # whatever is selected in the combo box
            click_event,
            list_variable_json, # StringVar with json string write traced to decode to update list
            name='',
            disable_var=None,
            debug_var=None,
            **kwargs
            ):

        super().__init__(parent, **kwargs)
        # self.list_variable = list()
        # if list_variable_json == None:
        #     list_variable_json = tk.StringVar(value="{}")
        self.list_variable_json = list_variable_json
        self.list_variable_json.trace_add('write', self._update_list_variable)

        ttk.Radiobutton(self, variable=variable, text="public-beta",
                        value="public-beta").pack(side=tk.LEFT, expand=True, fill='x')
        ttk.Radiobutton(self, variable=variable, text="devnet-beta", 
                        value="devnet-beta").pack(side=tk.LEFT, expand=True, fill='x')
        ttk.Radiobutton(self, variable=variable, text="other",
                        value="other").pack(side=tk.LEFT, expand=True, fill='x')
        combobox = ttk.Combobox(self, textvariable=combo_var,
                     postcommand=self._update_list_variable, justify="left"
                     )
        combobox.pack(side=tk.LEFT, expand=True, fill='x')
        combobox.bind("<<ComboboxSelected>>", self._debug_combobox_selected)
        self.variable = variable
        self.variable.widget = self
        self.variable.widget_combobox = combobox
        combobox.variable = combo_var
        combobox.variable.widget = self
        # a StringVar can contain a json string
        # a write trace can signal a call to this frame to update the list
                     # with its contents

    def _debug_combobox_selected(self, e, *_):
        e.widget.selection_clear()
        e.widget.variable.widget.variable.set("other")
        # print(e.widget.variable.get())
        # print(e.widget.get())

    def _update_list_variable(self, *_):
        decoded_to_list = json.loads(self.list_variable_json.get())
        self.variable.widget_combobox['values'] = decoded_to_list        # self.list_variable = json(self.list_variable_json.get()).decode()
        # decode the json string in self.list_variable_json and set self.list_variable

