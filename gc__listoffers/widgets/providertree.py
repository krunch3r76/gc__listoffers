import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from dataclasses import dataclass
from collections import UserDict
from decimal import Decimal, getcontext
from collections import namedtuple, UserList

from debug import logger

_percentExpand = 0.50

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

def find_column_offset(fieldname, fixed_field_list, column_placements):
    indexFieldname = fixed_field_list.index(fieldname)
    indexPlacement = column_placements.index(indexFieldname)
    return indexPlacement

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
        self._last_column_pressed = 0
        # self._last_column_pressed_label = ''
        self._state_dragging_column = False

        self.column_placements = [ i-1 for i in range(1,len(list(self.column_defs))) ]
        logger.debug(f"column_placements: {self.column_placements}")
        column_defs_dict = dict(self.column_defs.items())
        column_defs_dict.pop('#0')
        for key, value in column_defs_dict.items():
            self.column_defs[key]['label'] = key
        self.treeview=ttk.Treeview(self, columns=list())
        self.treeview['selectmode']='extended'
        self._set_column_headers()
        self.treeview.grid(sticky="news")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.treeview.bind("<Button-1>", self._on_drag_start)
        self.treeview.bind("<ButtonRelease-1>", self._on_drag_release)
        self.treeview.bind("<Motion>", self._on_motion)

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

        # ex on name
        longest_name = 'name'
        children_ids = self.treeview.get_children()
        if len(children_ids) > 0:
            indexPlacement = find_column_offset('name', list(self.column_defs.keys())[1:], self.column_placements)
            for id_ in children_ids:
                values = self.treeview.item(id_, option='values')
                field_value = values[indexPlacement]
                if len(field_value) > len(longest_name):
                    longest_name = field_value

        self.treeview.column('name', width=_measure(longest_name)) 

        # todo, lookup fixed widths for other columns and enforce


    def _swap_column_values(self, col1, col2):
        logger.debug(f"swapping {col1} values with {col2} values")
        col1_label = self.treeview.heading(col1)['text']
        col2_label = self.treeview.heading(col2)['text']
        logger.debug(f"swapping {col1_label} with {col2_label}")
        children = self.treeview.get_children()
        for iid in children:
            full_set = self.treeview.set(iid)
            #print(full_set)
            col1_value = self.treeview.set(iid, col1)
            # print(f"col1={col1}: {set_result}")
            col2_value = self.treeview.set(iid, col2)
            # print(f"col2={col2}: {set_result}\n")
            self.treeview.set(iid, col1, col2_value)
            self.treeview.set(iid, col2, col1_value)

    def _on_drag_start(self, event):
        widget = event.widget
        region = widget.identify_region(event.x, event.y)
        if region == "heading":
            self._state_dragging_column = True
            column = widget.identify_column(event.x)
            self._last_column_pressed = column
            # self._last_column_pressed_label = self.treeview.column(column)['id']
            self._last_column_pressed_label = self.treeview.heading(column)['text']
            logger.debug(f"button pressed on column: {self._last_column_pressed}: {self._last_column_pressed_label}")
        # else:
        #     return "break"

    def _on_motion(self, event):
        widget = event.widget
        region = event.widget.identify_region(event.x, event.y)
        if region == "separator":
            return "break"
        elif region == "heading" and self._state_dragging_column == True:
            column = widget.identify_column(event.x)
            if column != self._last_column_pressed:
                self._on_drag_release(event, motion=True)

    def _on_drag_release(self, event, motion=False):
        # check that this is a drag release
        if self._state_dragging_column == True:
            if motion==False:
                self._state_dragging_column = False
            widget = event.widget
            column = widget.identify_column(event.x)
            # column_label = self.treeview.column(column)['id']
            column_label = self.treeview.heading(column)['text']
            # self._swap_column_values(self._last_column_pressed, column)
            column_label_last = self.treeview.heading(self._last_column_pressed)['text']
            placement_column_last = find_column_offset(column_label_last, list(self.column_defs.keys())[1:], self.column_placements) # TODO make part of class so second argument not needed
            placement_column = find_column_offset(column_label, list(self.column_defs.keys())[1:], self.column_placements)
            logger.debug(self.column_placements)
            swap_list_elements(placement_column_last, placement_column, self.column_placements)
            logger.debug(self.column_placements)
            self.treeview.heading(self._last_column_pressed, text=column_label)
            self.treeview.heading(column, text=column_label_last)
            self._swap_column_values(self._last_column_pressed, column)
            self._update_column_header_widths() # temporary because name shall be fixed
            if motion==True:
                self._last_column_pressed = column
            # self._set_column_headers()

            for next_col in range(3,11):
                self._debug_sort(f"#{next_col}", top_iid_of_last_group=None)
            # self._debug_sort()

    def _debug_sort(self, col="#3", reverse=False, top_iid_of_last_group=None, sort_index=None):
        # logger.debug(col)
        # logger.debug(f"SORTING COL = {col}")
        end_of_iids = False
        tv = self.treeview
        sort_index = list()
        root_iid = None
        def conform(value, colnum):
            colText = tv.heading(colnum)
            if colText in ['cpu (/hr)', 'dur (/hr)', 'start', 'cores', 'threads', 'mem', 'storage']:
                value = Decimal(value)
            elif colText in [ 'frequency' ]:
                value = Decimal(value.strip('GHz'))
            elif colText in [ 'features' ]:
                value = Decimal('0.0')
            elif colText in [ 'version' ]:
                value = tuple(map(int, (v.spllit('.')))) # https://stackoverflow.com/a/11887825
            return value

        def list_of_preceding_column_values(iid, end_column_num, start_column=3):
            seq = list()
            end_column = int(end_column_num.strip('#'))
            for col_int in range(start_column,end_column):
                col_num = f"#{col_int}"
                seq.append(conform(tv.set(iid, col_num), col_num))
            return seq

        if col=='#3':
            for iid in tv.get_children(''):
                sort_value = conform(tv.set(iid, col), col) if col != '#0' else iid
                sort_index.append( (sort_value, iid, ) )
            sort_index.sort(reverse=reverse)

            for index, (_, iid) in enumerate(sort_index):
                tv.move(iid, '', index)

            next_col = int(col.strip('#'))+1
            first_iid = tv.get_children()[0]
            self._debug_sort(f"#{next_col}", top_iid_of_last_group=None)
        else:
            # implied top_iid_of_last_group provided
            # move down the columns for which the previous column values are the same
            #  as the first group
            if sort_index == None:
                sort_index = list()
            if top_iid_of_last_group==None:
                # top_iid_of_last_group = ''
                top_iid_of_last_group = next(iter(tv.get_children()))
            previous_column_int = int(col.strip('#'))-1
            previous_column_number = f"#{previous_column_int}"
            current_iid = tv.get_children()[0]
            indexoffset=0
            # traverse to beginning (top) of last group
            while current_iid != top_iid_of_last_group:
                current_iid = self.treeview.next(current_iid)
                indexoffset+=1

            k_prev_col_values_at_iid = list_of_preceding_column_values(top_iid_of_last_group, col)
            prev_col_values_at_current_iid = k_prev_col_values_at_iid

            while prev_col_values_at_current_iid == k_prev_col_values_at_iid:
                sort_value = conform(tv.set(current_iid, col), col)
                sort_index.append( (sort_value, current_iid, ) )
                current_iid = tv.next(current_iid)
                if current_iid == '':
                    end_of_iids = True
                    break
                else:
                    prev_col_values_at_current_iid = list_of_preceding_column_values(current_iid, col)

            # review this kludge
            # sort_index_backup=sort_index.copy()
            # sort_index.sort(reverse=reverse)
            # if sort_index_backup != sort_index:
            #     for index, (_, iid) in enumerate(sort_index):
            #         tv.move(iid, '', index + indexoffset)
            #     logger.debug(sort_index)
            #     last_element = sort_index[-1]
            #     last_iid = last_element[1]

            def do_sort(sort_index, indexoffset=0, clear=False):
                sort_index.sort(reverse=False, key=lambda x: x[0])
                for index, (_, iid) in enumerate(sort_index):
                    tv.move(iid, '', index + indexoffset)
                if clear:
                    sort_index.clear()


            if not end_of_iids:
                # logger.debug(current_iid)
                do_sort(sort_index, indexoffset)
                self._debug_sort(col, top_iid_of_last_group=current_iid, sort_index=None)


            # else: # move on to next column
            #     next_col = int(col.strip('#'))+1
            #     if next_col <= 10:
            #         # logger.debug(f"SORTING NEXT_COL = {next_col}")
            #         self._debug_sort(f"#{next_col}", top_iid_of_last_group=None)

    def _set_column_headers(self):


        self.treeview.grid_remove()
        ## convert to dict
        colDict = dict(self.column_defs.items())
        ## arrange dict
        arrDict = dict_as_arranged(colDict, self.column_placements)
        ## set columns
        logger.debug(list(arrDict.keys()))
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
        self._update_column_header_widths()
        self.treeview.grid()

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
            self.event_generate("<<Providerlist Updated>>")
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
