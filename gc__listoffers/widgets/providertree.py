import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from dataclasses import dataclass
from collections import UserDict
from decimal import Decimal, getcontext
from collections import namedtuple, UserList

from debug import logger

_percentExpand = 0.0

# the ProviderTree widget also holds abstractions of the data
# inserted than may be accessed by higher levels of the view
def _measure(text):
    import math
    # iterate over text and measure each character to identify longest
    longest_character_measure = 0
    longest_character = ' '
    s=ttk.Style()
    font_string = s.lookup('Treeview', 'font').split(' ')[0]
    font=tkfont.nametofont(font_string)
    lengths = []
    for c in text:
        m = font.measure(c)
        lengths.append(m)

    average_length=math.ceil(sum(lengths)/len(lengths))
    return average_length * len(text)
    # return longest_character_measure * len(text)

    # s=ttk.Style()
    # font_string = s.lookup('Treeview', 'font').split(' ')[0]
    # # font=tkfont.nametofont(font_string, window)
    # font=tkfont.nametofont(font_string)
    # measurement = font.measure(text)
    # return int(measurement)

InsertionTuple = namedtuple('InsertionTuple',
                            ['offerRowID', 'name', 'address', 'cpu_sec',
                             'duration_sec', 'fixed', 'cores',
                             'threads', 'version', 'most_recent_timestamp', 
                             'modelname', 'freq', 'token_kind', 'features',
                             'featuresFiltered',
                             'mem_gib', 'storage_gib', 'json'
                             ])


class InsertDict(UserDict):
    # notes, features will be used to compose a full list of unique features
    #filterable
    def __init__(self, merge: InsertionTuple, column_defs, column_placements=None):

        # representation of columns that may be inserted into the view, for
        #export to controller
        self.features = merge.features # revise to use filtered, and make as
        #list
        super().__init__()
        def remove_exponent(d):
            return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()
        getcontext().prec=8
        tdict = dict()
        tdict['rowId'] = merge.offerRowID
        tdict['paymentForm'] = merge.token_kind
        tdict['features'] = self.features # revise to curtail
        tdict['name'] = merge.name
        tdict['address'] = merge.address[0:8]
        tdict['cpu (/hr)'] = str(remove_exponent(
                Decimal(str(merge.cpu_sec))*Decimal('3600.0'))
                                 )
        tdict['dur (/hr)'] = str(remove_exponent(
                Decimal(str(merge.duration_sec))*Decimal('3600.0'))
                                 )
        tdict['start'] = merge.fixed
        tdict['cores'] = merge.cores
        tdict['threads'] = merge.threads
        tdict['frequency'] = merge.freq
        tdict['version'] = merge.version
        tdict['mem'] = merge.mem_gib
        tdict['storage'] = merge.storage_gib

        self.update(dict_as_arranged(column_defs, column_placements, tdict))




class ProviderTree(ttk.Frame):
    """
        .column_defs := fixed order of all possible columns and ttk
                            configurations
        .column_placements := offsets beginning with 1 to fixed columns
                                as defined by .column_defs
    """
    defaults = {
            'anchor': 'w',
            'minwidth': 40, # this can be expanded to fit the label
            #along with width
            'width': 40,
            'stretch': True
    }

    def __init__(
            self,
            parent,
            select_event,
            name='',
            disable_var=None,
            debug_var=None,
            **kwargs
            ):
        getcontext().prec=8
        super().__init__(parent, **kwargs)
        self.hiddencolumns = [0, 1]

        # self.insertionTuples = InsertionList()
        self.column_defs = { 
            '#0': { 'width': 0, 'minwidth': 0, 'stretch': False },
            'rowId': { },
            'paymentForm': { },
                            'name': { 'width': _measure("0x123456"), 'minwidth': _measure("0x123456"), 'stretch': False },
            'address': { # 'minwidth': _measure("0x123456"),
                         #'width': _measure("0x123456"),
                        },
            'cpu (/hr)': { },
            'dur (/hr)': { },
            'start': { },
            'cores': { },
            'threads': { },
            'frequency': { },
            'mem': { },
            'storage': { },
            'version': { },
            'features': { },
            }

        self._last_column_pressed = 0
        # self._last_column_pressed_label = ''
        self._state_dragging_column = False

        column_defs_dict = dict(self.column_defs.items())
        column_defs_dict.pop('#0')
        for key, value in column_defs_dict.items():
            self.column_defs[key]['label'] = key

        self.treeview=ttk.Treeview(self, columns=list(column_defs_dict.keys()))
        logger.debug(f"treeview columns: {self.treeview['columns']}")
        self.treeview['selectmode']='extended'
        self.treeview.column('#0', **self.column_defs['#0'])
        for name, definition in self.column_defs.items():
            if name != '#0':
                label = definition.get('label', '')
                anchor = definition.get('anchor', self.defaults['anchor'])
                minwidth = definition.get('minwidth', _measure(label))
                width = definition.get('width', minwidth)
                if minwidth > width:
                    width = minwidth
                stretch = definition.get('stretch', self.defaults['stretch'])
                self.treeview.heading(name, text=label, anchor=anchor)
                self.treeview.column(name, anchor=anchor, minwidth=minwidth,
                                     width=width, stretch=stretch)

        numdisplaycolumns = len(self._list_column_keys())
        displaycolumns_as_list = [ i for i in range(0,numdisplaycolumns-1) ]
        for hiddencolumn in self.hiddencolumns:
            displaycolumns_as_list.remove(hiddencolumn)

        self.treeview['displaycolumns'] = displaycolumns_as_list
        # self._set_column_headers()
        self.treeview.grid(sticky="news")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # self.treeview.bind("<Button-1>", self._on_drag_start)
        # self.treeview.bind("<ButtonRelease-1>", self._on_drag_release)
        # self.treeview.bind("<Motion>", self._on_motion)

        if debug_var != None:
            debug_var.trace_add('write', self._debug)

    def _list_column_keys(self):
        # may make a computed property
        return list(self.column_defs.keys())

    def insert(self, recordDict=None, last=False):
        def remove_exponent(d):
            return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()

        tv = self.treeview
        if not last:
            insertionDict = dict()
            # define lookup_table to map columns from array of possible input
            #keys
            lookup_table = {
                'rowId': [ 'offerRowID'] ,
                'paymentForm': [ 'token_kind' ],
                'name': [ 'name' ],
                'address': [ 'address' ],
                'cpu (/hr)': [ 'cpu_sec'],
                'dur (/hr)': [ 'duration_sec'],
                'start': [ 'fixed' ],
                'cores': [ 'cores' ],
                'threads': [ 'threads' ],
                'frequency': [ 'freq' ],
                'mem': [ 'mem_gib' ],
                'storage': [ 'storage_gib' ],
                'version': [ 'version' ],
                'features': [ 'features' ],
                    }

            # create insertion dictionary via lookup_table
            def search(list_value, dict_):
                # find the first key for which list_value occurs in the key's val
                # optimize by building a lookup table TODO
                corresponding_key = None
                for key, value_as_list in dict_.items():
                    if list_value in value_as_list:
                        corresponding_key = key
                        break
                return corresponding_key

            for key, value in recordDict.items():
                mapped_key = search(key, lookup_table)
                if mapped_key != None:
                    if mapped_key in ['cpu (/hr)', 'dur (/hr)']:
                        value = str(remove_exponent(Decimal(str(value))*Decimal('3600.0')))
                    elif mapped_key in ['address']:
                        value = value[0:8]

                    insertionDict[mapped_key] = value

            fixed_keys = self._list_column_keys()
            insertionSequence = list()
            for columnkey in self.treeview['columns']:
                insertionSequence.append(str(insertionDict[columnkey]))
            # for displaycolumn in self.treeview['columns']:
            #     corresponding_key = fixed_keys[displaycolumn+1]
            #     insertionSequence.append(str(insertionDict[corresponding_key]))

            # print(self.treeview['displaycolumns'])
            # print(insertionSequence)

            self.treeview.insert('', 'end', 
                                 iid=insertionDict['rowId'],
                                 values=insertionSequence
                                 )

        if last:
            logger.debug(tv.column('name'))
            logger.debug(tv.column('address'))
            longest_name = ''
            index_to_name = self._list_column_keys().index('name')-1
            for child in tv.get_children():
                values = tv.item(child)['values']
                # logger.debug(values)
                name = values[index_to_name]
                if len(str(name)) > len(longest_name):
                    longest_name = name
            measure_longest_name = _measure(longest_name)
            logger.debug(f"longest_name: {longest_name}")
            logger.debug(f"longest_name measure: {measure_longest_name}")
            if measure_longest_name > tv.column('name')['minwidth']:
                tv.column('name', minwidth=measure_longest_name, width=measure_longest_name)
            logger.debug(tv.column('name'))
            logger.debug(tv.column('address'))
    def _debug(self, *_):
        # primarily for debugging visual placement
        print("DEBUG FROM PROVIDERTREE")
        try:
            self["borderwidth"] = 2
            self['relief']='solid'
        except:
            pass
