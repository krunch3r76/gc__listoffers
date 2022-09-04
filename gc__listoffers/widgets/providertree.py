import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from dataclasses import dataclass
from collections import UserDict
from decimal import Decimal, getcontext
from collections import namedtuple, UserList

_percentExpand = 0.5

# the ProviderTree widget also holds abstractions of the data
# inserted than may be accessed by higher levels of the view

InsertionTuple = namedtuple('InsertionTuple',
                            ['offerRowID', 'name', 'address', 'cpu_sec',
                             'duration_sec', 'fixed', 'cores',
                             'threads', 'version', 'most_recent_timestamp', 
                             'modelname', 'freq', 'token_kind', 'features',
                             'featuresFiltered',
                             'mem_gib', 'storage_gib', 'json'
                             ])

def dict_as_arranged(fixed_dict, column_placements, replacement_dict=None):
    """
        fixed_dict     fixed ordered dict to which column_placements place refers
        column_placements   offsets corresponding to column_defs (excluding #0)
        replacement_dict optional values to copy in place of fixed dict
    """
    newDict = dict()
    # fixed_as_list = list(fixed_dict)[1:] # keys only
    fixed_as_list = list(fixed_dict.keys())[1:]
    if replacement_dict == None:
        replacement_dict = fixed_dict
    for offset in column_placements:
        # add key:value pairs in newly arranged order
        key_at_placement = fixed_as_list[offset]
        newDict[key_at_placement] = replacement_dict[key_at_placement]
    
    return newDict


def swap_list_elements(offset1, offset2, list_):
    # modifies input list such that values at offset1,2 are swapped
    save_offset1 = list_[offset1]
    list_[offset1] = list_[offset2]
    list_[offset2] = save_offset1

def manufacture_row(insertionTuple):
    pass

def _measure(text, window=None):
    s=ttk.Style()
    font_string = s.lookup('Treeview', 'font').split(' ')[0]
    # font=tkfont.nametofont(font_string, window)
    font=tkfont.nametofont(font_string)
    measurement = font.measure(text)
    return int(measurement + measurement * _percentExpand)

class InsertDict(UserDict):
    # notes, features will be used to compose a full list of unique features filterable
    def __init__(self, merge: InsertionTuple, column_defs, column_placements=None):

        # representation of columns that may be inserted into the view, for export
        # to controller
        self.features = merge.features # revise to use filtered, and make as list
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
        tdict['cpu (/hr)'] = str(remove_exponent(Decimal(str(merge.cpu_sec))*Decimal('3600.0')))
        tdict['dur (/hr)'] = str(remove_exponent(Decimal(str(merge.duration_sec))*Decimal('3600.0')))
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
            'minwidth': 40, # this can be expanded to fit the label along with width
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
        super().__init__(parent, **kwargs)
        self.hiddencolumns = [0, 1]
        # self.insertionTuples = InsertionList()
        self.column_defs = { 
            '#0': { 'width': 0, 'minwidth': 0, 'stretch': False },
            'rowId': { },
            'paymentForm': { },
                            'name': {'width': _measure("0x123456"), 'stretch': False },
            'address': { 'minwidth': _measure("0x123456"),
                         'width': _measure("0x123456"),
                         'stretch': False
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
        self.column_placements = [ i-1 for i in range(1,len(list(self.column_defs))) ]
        column_defs_dict = dict(self.column_defs.items())
        column_defs_dict.pop('#0')
        for key, value in column_defs_dict.items():
            self.column_defs[key]['label'] = key
        self.treeview=ttk.Treeview(self, columns=list())
        self._set_column_headers()
        self.treeview.grid(sticky="news")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        if debug_var != None:
            debug_var.trace_add('write', self._debug)

    def _displaycolumns(self):
        # return set difference of columns and non-display columns
        # in: .hiddencolumns, .column_placements
        # out: displaycolumns 
        displaycolumns = list()
        for column_placement in self.column_placements:
            if column_placement not in self.hiddencolumns:
                displaycolumns.append(column_placement)

        return displaycolumns

    def _update_column_header_widths(self):
        # check children and reconfigure column widths as needed
        def find_field_offset(fieldname, fixed_field_list, column_placements):
            indexFieldname = fixed_field_list.index(fieldname)
            indexPlacement = column_placements.index(indexFieldname)
            return indexPlacement

        # ex on name
        longest_name = 'name'
        children_ids = self.treeview.get_children()
        if len(children_ids) > 0:
            indexPlacement = find_field_offset('name', list(self.column_defs.keys())[1:], self.column_placements)
            for id_ in children_ids:
                values = self.treeview.item(id_, option='values')
                field_value = values[indexPlacement]
                if len(field_value) > len(longest_name):
                    longest_name = field_value

        self.treeview.column('name', width=_measure(longest_name)) 
    def _set_column_headers(self):
        # TODO adjust lengths?
        ## convert to dict
        colDict = dict(self.column_defs.items())
        ## arrange dict
        arrDict = dict_as_arranged(colDict, self.column_placements)
        ## set columns
        self.treeview['columns'] = list(arrDict.keys())
        self.treeview['displaycolumns'] = self._displaycolumns()

        ## define columns
        self.treeview.column('#0', **self.column_defs['#0'])
        for name, definition in arrDict.items():
            label = definition.get('label', '')
            anchor = definition.get('anchor', self.defaults['anchor'])
            minwidth = definition.get('minwidth', _measure(label,
                                                           window=self.treeview))
            width = definition.get('width', minwidth)
            if minwidth > width:
                width=minwidth
            stretch = definition.get('stretch', self.defaults['stretch'])
            self.treeview.heading(name, text=label, anchor=anchor)
            self.treeview.column(name, anchor=anchor, minwidth=minwidth,
                                 width=width, stretch=stretch)
        # self.treeview.column('name', width=_measure(self.insertionTuples.longestname))

        # self._insert_rows()
        # self.treeview.grid(sticky="news")

        
    # def _draw(self):
    #     try:
    #         self.treeview.grid_forget()
    #     except:
    #         pass
    #     self.treeview=ttk.Treeview(self, columns=list())
    #     ## convert to dict
    #     colDict = dict(self.column_defs.items())
    #     from pprint import pprint
    #     pprint(colDict)
        
    #     # colDict.pop('#0')
    #     ## arrange dict
    #     print(f"column placements: {self.column_placements}")
    #     arrDict = dict_as_arranged(colDict, self.column_placements)
    #     pprint(arrDict)
    #     ## set columns
    #     pprint(arrDict.keys())
    #     self.treeview['columns'] = list(arrDict.keys())

    #     # hidden_column_placements = [ 1 ]
    #     # hidden_column_placements.append(0)
    #     # display_columns = list()
    #     # for column_placement in self.column_placements:
    #     #     if column_placement not in hidden_column_placements:
    #     #         display_columns.append(column_placement)
    #     self.treeview['displaycolumns'] = self._displaycolumns()

    #     ## define columns
    #     self.treeview.column('#0', **self.column_defs['#0'])
    #     for name, definition in arrDict.items():
    #         label = definition.get('label', '')
    #         anchor = definition.get('anchor', self.defaults['anchor'])
    #         minwidth = definition.get('minwidth', _measure(label,
    #                                                        window=self.treeview))
    #         width = definition.get('width', minwidth)
    #         if minwidth > width:
    #             width=minwidth
    #         stretch = definition.get('stretch', self.defaults['stretch'])
    #         self.treeview.heading(name, text=label, anchor=anchor)
    #         self.treeview.column(name, anchor=anchor, minwidth=minwidth,
    #                              width=width, stretch=stretch)
    #     print(f"longest name is: {self.insertionTuples.longestname}")
    #     self.treeview.column('name', width=_measure(self.insertionTuples.longestname))

    #     self._insert_rows()
    #     self.treeview.grid(sticky="news")

    def _insert_rows(self):
        """
            inputs                  process
            .insertionTuples        on each insertionTuple
            .treeview                   as InsertionDict (iDict)
            .column_defs                .treeview.insert(...)
            .column_placements
        """
        longestName = ''
        for iTuple in self.insertionTuples:
            iDict = InsertDict(iTuple, self.column_defs, self.column_placements)
            self.treeview.insert('', 'end', iid=iDict['rowId'], values=list(iDict.data.values()))

    def insert(self, recordTuple=None, last=False):
        if recordTuple != None:
            ## conform InsertionTuple
            insertionTuple = InsertionTuple(**recordTuple)
            iDict = InsertDict(insertionTuple, self.column_defs, self.column_placements)
            self.treeview.insert('', 'end', iid=iDict['rowId'], values=list(iDict.data.values()))

            ## append
            # self.insertionTuples.append(insertionTuple)
            # ## convert to InsertDict
            # insertionDict = InsertDict(insertionTuple, self.column_defs, self.column_placements) 
        elif last == True:
            ## insert row
            # self.treeview.insert('', 'end', iid=insertionDict['rowId'], values=list(insertionDict.data.values()))
            self._update_column_header_widths()
        else:
            raise ValueError

    def _debug(self, *_):
        # primarily for debugging visual placement
        print("DEBUG FROM PROVIDERTREE")
        try:
            self["borderwidth"] = 2
            self['relief']='solid'
        except:
            pass


if __name__ == '__main__':
    root=tk.Tk()
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    from pathlib import Path
    projectdir = Path(__file__).parent.parent.parent
    root.tk.call(
        "source", str(projectdir / "forest-ttk-theme/forest-light.tcl")
    )
    s=ttk.Style()
    s.theme_use("forest-light")
    pt=ProviderTree(root, '')
    pt.insert(debugInsertDict)
    import tkinter.font as tkfont
    root.mainloop()
