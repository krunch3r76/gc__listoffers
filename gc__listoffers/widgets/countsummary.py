
import tkinter as tk
from tkinter import ttk
import json

_DIC544 = "#4D4D4D"
# eeeeee
class CountSummary(ttk.Frame):
    """
    """
    def __init__(
            self,
            parent,
            totalCount,
            glmNodeCount,
            tglmNodeCount,
            font="TkDefaultFont 10",
            foregroundcolor = _DIC544,
            name='',
            disable_var=None,
            debug_var=None,
            **kwargs
            ):

        super().__init__(parent, **kwargs)
        
        def font_2x(fontstr):
            index_to_space_str = fontstr.rfind(' ')
            index_to_space = int(index_to_space_str)
            doubled = int(fontstr[index_to_space+1:]) * 2
            return fontstr[:index_to_space+1] + str(doubled)

        ttk.Label(self, textvariable=totalCount, foreground=foregroundcolor, font=font_2x(font)
                  ).grid(row=0, column=1)
        ttk.Label(self, textvariable=glmNodeCount, foreground=foregroundcolor, font=font
                  ).grid(row=1, column=0)
        ttk.Label(self, text="|", foreground=foregroundcolor, font=font
                  ).grid(row=1, column=1)
        ttk.Label(self, textvariable=tglmNodeCount, foreground=foregroundcolor, font=font
                  ).grid(row=1, column=2)

        
    def _debug_combobox_selected(self, e, *_):
        e.widget.selection_clear()
        e.widget.variable.widget.variable.set("other")
        # print(e.widget.variable.get())
        # print(e.widget.get())

    def _update_list_variable(self, *_):
        decoded_to_list = json.loads(self.list_variable_json.get())
        self.variable.widget_combobox['values'] = decoded_to_list        # self.list_variable = json(self.list_variable_json.get()).decode()
        # decode the json string in self.list_variable_json and set self.list_variable

