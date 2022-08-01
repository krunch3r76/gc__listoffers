import tkinter as tk

class Variables(dict):
    def __init__(self):
        """pre: root window instantiated"""
        self.filters = dict()
        self['filters'] = self.filters

        self['debug_var']=tk.BooleanVar(value=False)
        self['disable_var']=tk.BooleanVar(value=False)

        self['filters']['max_cpu_checkVar']=tk.BooleanVar(value=False)
        self['filters']['max_cpu_entryVar']=tk.DoubleVar(value="23.5")
        self['filters']['max_dur_checkVar']=tk.BooleanVar(value=False)
        self['filters']['max_dur_entryVar']=tk.DoubleVar(value="1234")
        self['filters']['start_checkVar']=tk.BooleanVar(value=False)
        self['filters']['start_entryVar']=tk.DoubleVar(value='0.0')
        self['filters']['feature_checkVar']=tk.BooleanVar(value=False)
        self['filters']['feature_entryVar']=tk.StringVar(value='')
        self['probe_checkVar']=tk.BooleanVar(value=False)


