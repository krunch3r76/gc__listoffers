import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from dataclasses import dataclass
from collections import UserDict

from collections import namedtuple
# InsertionTuple used to enforce agreement with records added via controller
# irrelevant: most_recent_timestamp, highest_version
InsertionTuple = namedtuple('InsertionTuple',
                            ['offerRowID', 'name', 'address', 'cpu_sec', 'duration_sec', 'fixed', 'cores',
                             'threads', 'version', 'most_recent_timestamp', 
                             'modelname', 'freq', 'token_kind', 'features', 'featuresFiltered',
                             'mem_gib', 'storage_gib', 'json'
                             ])

def dict_as_arranged(fixed_dict, column_placements, replacement_dict=None):
    """
        fixed_dict     fixed ordered dict to which column_placements place refers
        column_placements   offsets corresponding to column_defs
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

def manufacture_row(insertionTuple):
    pass
def _measure(text, window=None):
    s=ttk.Style()
    font_string = s.lookup('Treeview', 'font').split(' ')[0]
    # font=tkfont.nametofont(font_string, window)
    font=tkfont.nametofont(font_string)
    return font.measure(text)

class InsertDict(UserDict):
    # notes, features will be used to compose a full list of unique features filterable
    def __init__(self, merge: InsertionTuple, column_defs, column_placements=None):

        # representation of columns that may be inserted into the view, for export
        # to controller
        self.features = merge.features # revise to use filtered, and make as list
        super().__init__()
        # {
        #     'rowId' : merge.offerRowID,
        #     'paymentForm' : merge.token_kind,
        #     'features' : self.features,# revise to curtail
        #     'name' : merge.name,
        #     'address' : merge.address,
        #     'cpu (/hr)' : str(float(merge.cpu_sec)*3600.0),
        #     'dur (/hr)' : str(float(merge.duration_sec)*3600.0),
        #     'start' : merge.fixed,
        #     'cores' : merge.cores,
        #     'threads' : merge.threads,
        #     'frequency' : merge.freq,
        #     'version' : merge.version,
        #     'mem' : merge.mem_gib,
        #     'storage' : merge.storage_gib
        #         })
        # super().__init__({
        #         'rowId': None, 'name': None, 'address': None, 'cpu (/hr)': None, 'dur (/hr)': None,
        #         'cores': None, 'threads': None, 'frequency': None, 'version': None, 'mem': None,
        #         'storage': None, 'features': None
        #         })

        tdict = dict()
        tdict['rowId'] = merge.offerRowID
        tdict['paymentForm'] = merge.token_kind
        tdict['features'] = self.features # revise to curtail
        tdict['name'] = merge.name
        tdict['address'] = merge.address
        tdict['cpu (/hr)'] = str(float(merge.cpu_sec)/3600.0)
        tdict['dur (/hr)'] = str(float(merge.duration_sec)/3600.0)
        tdict['start'] = merge.fixed
        tdict['cores'] = merge.cores
        tdict['threads'] = merge.threads
        tdict['frequency'] = merge.freq
        tdict['version'] = merge.version
        tdict['mem'] = merge.mem_gib
        tdict['storage'] = merge.storage_gib

        self.update(dict_as_arranged(column_defs, column_placements, tdict))
        # column_defs_as_list = list(column_defs)[1:]
        # for offset in column_placements:
        #     key_at_placement = column_defs_as_list[offset]
        #     self[key_at_placement] = tdict[key_at_placement]

        
#        self.update(merge)

def insert_dict_from_tuple(insertionTuple):
    """
        create an insertion row sequence including computed properties from an insertion
        tuple
    """
    pass

# debugInsertDict = InsertDict({
#         'rowId': '1234', 'name': "supercalifragilistic expealidocious even tho the sound of it", 'address': '0x1234', 'cpu (/hr)': '1.2345', 'dur (/hr)': '5.4321',
#         'cores': '8', 'threads': '16', 'frequency': '4Ghz', 'version': '0.10.1', 'mem': '1.234',
#         'storage': '4.321'
#     }
#         )


class ProviderTree(ttk.Frame):

    _percentExpand=0.5
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
        self.insertionTuples = list()
        self.column_defs = {
            '#0': { },
            'rowId': { },
            'paymentForm': { },
            'features': { },
            'name': {  'minwidth': 200, 'stretch': True },
            'address': { 'minwidth': int(_measure("0x12345")),
                         'width': int(_measure("0x12345")),
                         'stretch': False
                        },
            'cpu (/hr)': { },
            'dur (/hr)': { },
            'start': { },
            'cores': { },
            'threads': { },
            'frequency': { },
            'version': { },
            'mem': { },
            'storage': { },
            }
        self.column_placements = [ i for i in range(len(list(self.column_defs))-1) ]
                                
        column_defs_dict = dict(self.column_defs.items())
        column_defs_dict.pop('#0')
        for key, value in column_defs_dict.items():
            self.column_defs[key]['label'] = key
        self.treeview=ttk.Treeview(self, columns=list(self.column_defs.keys())[1:])
        
        for name, definition in self.column_defs.items():
            label = definition.get('label', '')
            anchor = definition.get('anchor', self.defaults['anchor'])
            minwidth = definition.get('minwidth', _measure(label,
                                                           window=self.treeview))
            minwidth += int(self._percentExpand * minwidth)
            width = definition.get('width', minwidth)
            if minwidth > width:
                width=minwidth
            stretch = definition.get('stretch', self.defaults['stretch'])
            self.treeview.heading(name, text=label, anchor=anchor)
            self.treeview.column(name, anchor=anchor, minwidth=minwidth,
                                 width=width, stretch=stretch)

        self.treeview.grid(sticky="news")
        # labels=[ value['label'] for value in self.column_defs.values() ][1:] 
        self.grid(sticky="news")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        if debug_var != None:
            debug_var.trace_add('write', self._debug)

    def insert(self, rowdict):
        """
            inputs                 process                         output
            rowdict                conform InsertionTuple 
                                   append
                                   convert to InsertDict
                                   insert row
        """
        ## conform InsertionTuple
        insertionTuple = InsertionTuple(**rowdict)
        ## append
        self.insertionTuples.append(insertionTuple)
        ## convert to InsertDict
        insertionDict = InsertDict(insertionTuple, self.column_defs, self.column_placements) 
        ## insert row
        self.treeview.insert('', 'end', iid=insertionDict['rowId'], values=list(insertionDict.data.values()))

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
