# from .get_datadir import get_datadir
# from .serve import run_server
from . offer_lookup import OfferLookup
import tkinter as tk

class Variables(dict):
    def __init__(self):
        """pre: root window instantiated"""
        self.filters = dict()
        self.counts = dict()
        self['filters'] = self.filters
        self['counts'] = self.counts

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
        self['probe_checkVar']=tk.IntVar(value=0)
        self['subnet_radioVar']=tk.StringVar(value='public-beta')
        self['subnet_list_json']=tk.StringVar(value='[]')
        self['subnet_comboVar']=tk.StringVar()
        self['latest_checkVar']=tk.IntVar(value=0)
        self['counts']['glmNodes']=tk.IntVar(value=0)
        self['counts']['tglmNodes']=tk.IntVar(value=0)
        self['counts']['totalNodes']=tk.IntVar(value=0)


