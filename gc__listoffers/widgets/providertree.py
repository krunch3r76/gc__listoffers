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



def _on_event(event, fnc):
    widget = event.widget
    region = widget.identify_region(event.x, event.y)
    column = widget.identify_column(event.x)

    return fnc(event, widget, region, column)




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
        self.parent=parent # can just use internal tk function for this ...

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

        self.treeview.bind("<Button-1>", lambda event: _on_event(event, self._on_drag_start))
        self.treeview.bind("<ButtonRelease-1>", lambda event: _on_event(event, self._on_drag_release))
        self.treeview.bind("<Motion>", lambda event: _on_event(event, self._on_motion))

        if debug_var != None:
            debug_var.trace_add('write', self._debug)


    def _on_drag_start(self, event, widget, region, column=None):
        logger.debug(f"column pressed: {column}")
        if region == "separator":
            return "break"
        elif region == "heading":
            if column not in [ "#1", "#2"]:
                self._state_dragging_column = True
                self._last_column_pressed = column
            else:
                self._sort_columns(column)

            return "break"
            # logger.debug(self.treeview.heading(column)['text'])

    def _on_motion(self, event, widget, region, column=None):
        if region == "separator":
            return "break"
        elif region == "heading" and self._state_dragging_column == True:
            pass
            if column != self._last_column_pressed:
                self._swap_columns(self._last_column_pressed, column)
                self._last_column_pressed = column
                tk._default_root.geometry(tk._default_root.geometry())
                return "break"

    def _on_drag_release(self, event, widget, region, column=None, moving=False):
        if self._state_dragging_column:
            self._state_dragging_column = False
            self._sort_columns()

        # if self._state_dragging_column == True and column != self._last_column_pressed:
        #     self._state_dragging_column = False

    def _sort_columns(self, col="#1"):
        # sort columns from left to right

        # process
        #  each row
        #   dict displayed
        #   normalize
        #   list
        #   sort

        tv = self.treeview
        sort_index = []


        def build_sort_index():
            def normalize_value(colname, value):
                normalized_value = None
                if colname in ['cpu (/hr)', 'dur (/hr)', 'start', 'cores', 'threads', 'mem', 'storage']:
                    normalized_value = Decimal(value)
                elif colname in [ 'frequency' ]:
                    if value == '':
                        stripped_freq = '0.0'
                    else:
                        stripped_freq = value.strip('GHz')
                    normalized_value = Decimal(stripped_freq)
                elif colname in [ 'features' ]:
                    normalized_value = Decimal('0.0')
                elif colname in [ 'version' ]:
                    normalized_value = tuple(map(int, (value.split('.')))) # https://stackoverflow.com/a/11887825
                else:
                    normalized_value = value
                return normalized_value

            for iid in tv.get_children(''):
                all_column_values_dict = tv.set(iid)
                # this assumes column headings match internal definitions
                _displayed_dict = dict([ ( list(all_column_values_dict.keys())[displayed_index], list(all_column_values_dict.values())[displayed_index], ) for displayed_index in tv['displaycolumns'] ])
                # logger.debug(_displayed_dict)
                normalized_row = []
                if col not in [ "#1", "#2" ]:
                    for colname, value in _displayed_dict.items():
                        if colname in [ 'name', 'address' ]:
                            continue
                        normalized_value = normalize_value(colname, value)
                        normalized_row.append(normalized_value)
                else:
                    displayed_dict_list = list(_displayed_dict.values())[0:2]
                    if col == "#1":
                        normalized_value = displayed_dict_list[0]
                    else:
                        normalized_value = displayed_dict_list[1]
                    normalized_row.append(normalized_value)
                sort_index.append( (normalized_row, iid, ) )
            return sort_index
        
        sort_index = build_sort_index()
        sort_index.sort(reverse=False)

        for index, (_, iid) in enumerate(sort_index):
            tv.move(iid, '', index)
                
                # logger.debug(keys_of_cols_displayed)
                # sort_values_displayed = [ index-1 for index in tv['displaycolumns'] ]

    def _column_dict(self):
        # map name to internal column offset
        column_keys = self._list_column_keys()[1:]
        column_keys.pop(0)
        mappings = dict()
        for i, column_key in enumerate(column_keys):
            mappings[column_key] = i+1
        return mappings
        # return dict(zip(column_keys, list(self.column_defs.keys())[1:]))

    def _swap_columns(self, col1, col2):
        # ...
        column_label = self.treeview.heading(col2)['text']
        column_label_prior = self.treeview.heading(
                col1
                )['text']
        mappings = self._column_dict()
        internal_col_to_first = mappings[column_label]
        internal_col_to_second = mappings[column_label_prior]
        display_columns_list = list(self.treeview['displaycolumn'])
        offset_to_displayed_1 = display_columns_list.index(internal_col_to_first)
        offset_to_displayed_2 = display_columns_list.index(internal_col_to_second)
        save = display_columns_list[offset_to_displayed_1]
        display_columns_list[offset_to_displayed_1] = display_columns_list[offset_to_displayed_2]
        display_columns_list[offset_to_displayed_2] = save

        self.treeview.configure(displaycolumns=display_columns_list)

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

            self.treeview.insert('', 'end', 
                                 iid=insertionDict['rowId'],
                                 values=insertionSequence
                                 )

        if last:
            # logger.debug(tv.column('name'))
            # logger.debug(tv.column('address'))
            longest_name = ''
            index_to_name = self._list_column_keys().index('name')-1
            for child in tv.get_children():
                values = tv.item(child)['values']
                # logger.debug(values)
                name = values[index_to_name]
                if len(str(name)) > len(longest_name):
                    longest_name = name
            measure_longest_name = _measure(longest_name)
            if measure_longest_name > tv.column('name')['minwidth']:
                tv.column('name',
                          minwidth=measure_longest_name,
                          width=measure_longest_name)
            # logger.debug(tv.column('name'))
            # logger.debug(tv.column('address'))

    def _debug(self, *_):
        # primarily for debugging visual placement
        try:
            self["borderwidth"] = 2
            self['relief']='solid'
        except:
            pass
