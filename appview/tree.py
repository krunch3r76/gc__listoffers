from tkinter import ttk
from tkinter import *
from tkinter import font
from functools import singledispatchmethod
import enum

import debug

class CustomTreeview(ttk.Treeview):
    """notes:
        #2 refers to the first column, which is always name
        #3 refers to the second column, which is always address
        the rest are variable
        summary: subtract 1 to get the corresponding index
    """

    class Field(enum.IntEnum):
        offerRowID=0
        name=1
        address=2
        cpu_per_hr=3
        dur_per_hr=4
        fixed=5
        cores=6
        threads=7
        version=8

    class StateHolder:
        __swapping = False
        __drag_start_column_number = ''

        def __init__(self):
            pass

        def whether_swapping(self):
            """indicates if a column has been dragged out of its last place"""
            return self.__swapping

        
        def transition_swapping(self, truthy: bool, drag_from=''):
            if not truthy:
                self.__drag_start_column_number=''
            else:
                assert drag_from != '', "expected a column number if swapping state being updated"
                self.__drag_start_column_number=drag_from

            self.__swapping=truthy
        @property
        def drag_start_column_number(self):
            # assert self.__swapping==True, "no column being dragged but queried for start"
            return self.__drag_start_column_number
        @drag_start_column_number.setter
        def set_drag_start_column_number(self, colstr : str):
            assert istype(colstr)==str, "colstr input as non-string"
            self.__drag_start_column_number=colstr
        


    # note, the first offset is the rownum
    _stateHolder = StateHolder()

    _heading_map = [ 0, 1, 2, 3, 4, 5, 6, 7, 8 ]
    _kheadings = ('offerRowID', 'name','address','cpu (/hr)', 'duration (/hr)', 'fixed', 'cores', 'threads', 'version')
    _kheadings_init = ( '0', '1', '2', '3', '4', '5', '6', '7', '8' )
    _kheadings_sql_paths = (
        None
        , "'node.id'.name"
        , "'offers'.address"
        , "'com.pricing.model.linear.coeffs'.cpu_sec"
        , "'com.pricing.model.linear.coeffs'.duration_sec"
        , "'com.pricing.model.linear.coeffs'.fixed"
        , "'inf.cpu'.cores"
        , "'inf.cpu'.threads"
        , "'runtime'.version"
            )
    _order_by_other = False




    def __build__update_cmd(self):
        """create a lookup table of callbacks and return"""
        """post: self._update_cmd_dict"""
        update_cmd_dict={
            "name": {"sort_on": "'node.id'.name"}
            , "address": {"sort_on": "'offers'.address"}
            , "cpu (/hr)": {}
            , "duration (/hr)": {}
            , "fixed": {}
            , "cores": {}
            , "threads": {}
            , 'version': {}
                }
        return update_cmd_dict




    def __init__(self, ctx, *args, **kwargs):
        """constructor for CustomTreeView"""
        """post:
            _ctx                :   AppView contextual parent
            _update_cmd_dict    :   callback lookup table

            buttons bound
            column options set
            
        """

        # initialize super with columns
        kwargs['columns']=self._kheadings_init
        super().__init__(*args, **kwargs)
        self._ctx = ctx
        self._update_cmd_dict = self.__build__update_cmd()
        # set mouse button bindings
        self.bind("<Button-1>", self.on_drag_start)
        self.bind("<B1-Motion>", self.on_drag_motion)
        self.bind("<ButtonRelease-1>", self.on_drag_release)

        self.bind("<<TreeviewSelect>>", self.on_select)

        # hide node, offerRowID columns
        self.column('#0', width=0, stretch=NO)
        self.column('0', width=0, stretch=NO) # offerRowID
        # setup visible columns
        self.column(1, width=0, anchor='w')
        self.column(2, width=0)
        # self.column(2, width=font.nametofont('TkHeadingFont').actual()['size']*8, anchor='w')
        #self.column(2, minwidth=font.nametofont('TkDefaultFont').actual()['size']*43)
        debug.dlog(font.nametofont('TkHeadingFont').configure())
        for index in range(3,len(self._kheadings_init)):
            self.column(index, width=0, anchor='w')
        # debug.dlog(f"internal columns: {self['columns']}")
        self._update_headings()



    def list_selection_addresses(self):
        """extract the node address values from the selection and return as a list or empty list"""
        thelist = []
        for item_id in self.selection():
            thelist.append(
                (
                    self.item(item_id)['values'][CustomTreeview.Field.offerRowID],
                    self.item(item_id)['values'][CustomTreeview.Field.address]
                )
                    )
            # print(self.item(item_id)['values'])
        return thelist







    def on_select(self, e):
        """TODO"""
        count_selected = len(self.selection())
        debug.dlog(f"count selected: {count_selected}")
        debug.dlog(self.list_selection_addresses())
        #self._ctx.count_selected.set(count_selected)
        self._ctx.count_selected=count_selected
            # debug.dlog(self.item(item_id)['values'])
        """
        debug.dlog(selections)
        debug.dlog(self.selection())

        debug.dlog(f"{self.focus()}")
        debug.dlog(f"{dir(e)}")
        debug.dlog(e)
        debug.dlog(e.widget())
        debug.dlog( self.item(self.focus() )  )
        #debug.dlog(self.item(args[0]))
        """
    def _model_sequence_from_headings(self):
        """follow the order of the headings to return a tuple of strings corresponding to the model table.column addresses"""
        """analysis
        the current ordering is found in self._heading_map, which lists pointer indices
        _kheadings_sql_paths contain the sql path at the corresponding indices
        we are not interested at this time in anything before 'cpu (/hr)', so we start at index 3
        """
        t = ()
        for index in range(3, len(self._heading_map)):
            heading_index = self._heading_map[index]
            t+=(self._kheadings_sql_paths[heading_index],)
        return t




    def _update_headings(self):
        """update headings with built in commands, called after a change to the heading order"""
        # debug.dlog(f"updating headings using heading map {self._heading_map}")
        def build_lambda(key):
            # return lambda *args: self._ctx._update_cmd(self._update_cmd_dict[key])
            return lambda : self._ctx._update_cmd(self._update_cmd_dict[key])

        for i, key in enumerate(self._update_cmd_dict.keys()):
            colno=i+1
            offset=self._kheadings.index(key)
            colno=self._heading_map.index(offset)
            self.heading(colno
                    , text=key
#                    , command=build_lambda(key)
                    , anchor='w'
                    )



    def on_drag_start(self, event):
        widget = event.widget
        region = widget.identify_region(event.x, event.y)
        # debug.dlog(region, 2)
        if region == "heading":
            widget._drag_start_x=event.x
            widget._drag_start_y=event.y
            self._stateHolder.transition_swapping(True, widget.identify_column(event.x) )
            self._drag_start_column_number=widget.identify_column(event.x) # TODO move to state object
        else:
            self._stateHolder.transition_swapping(False)
            self._drag_start_column_number=None


    def on_drag_motion(self, event):
        """swap columns when moved into a new column (except where restricted)"""
        widget = event.widget
        region = widget.identify_region(event.x, event.y)
        # debug.dlog(region, 3)
        if region == "heading":
        # x = widget.winfo_x() - widget._drag_start_x + event.x
        # y = widget.winfo_y() - widget._drag_start_y + event.y
            if self._stateHolder.whether_swapping():
                drag_motion_column_number = widget.identify_column(event.x)
                if drag_motion_column_number not in ("#2", "#3") and self._stateHolder.drag_start_column_number not in ("#2", "#3"):
                    if self._stateHolder.drag_start_column_number != drag_motion_column_number:
                        self._swap_numbered_columns(self._stateHolder.drag_start_column_number, drag_motion_column_number)


    def on_drag_release(self, event):
        """update display when a column has been moved (assumed non-movable columns not moved)"""
        widget = event.widget
        region = widget.identify_region(event.x, event.y)
        if region == "heading":
        # x = widget.winfo_x() - widget._drag_start_x + event.x
        # y = widget.winfo_y() - widget._drag_start_y + event.y

            curcol=widget.identify_column(event.x)
            if self._stateHolder.drag_start_column_number not in ("#2", "#3") and curcol not in ("#2", "#3"): # kludgey
                self._ctx._update_cmd()
            elif self._stateHolder.drag_start_column_number == curcol:
                if curcol=="#2":
                    self._ctx._update_cmd(self._update_cmd_dict['name'])
                else:
                    self._ctx._update_cmd(self._update_cmd_dict['address'])
            else:
                self._ctx._update_cmd()
        elif self._stateHolder.whether_swapping():
            self._stateHolder.transition_swapping(False)
            self._ctx._update_cmd()



    def _values_reordered(self, values):
        """convert the standard values sequence into the internal sequence and return"""
        # debug.dlog(values,3)
        l = [None for _ in self._heading_map ] 
        for idx, value in enumerate(values):
            newoffset=self._heading_map.index(idx)
            l[newoffset]=value
        return tuple(l)



    def _swap_numbered_columns(self, numbered_col, numbered_col_other):
        """reorder _heading_map based on inputs that came from .identify_column on drag event
        note: does not change contents of underlying rows, if any
        """
        debug.dlog(f"swapping {numbered_col} with {numbered_col_other}")
        # convert to heading offset
        numbered_col_internal = int(numbered_col[1])-1
        numbered_col_other_internal = int(numbered_col_other[1])-1


        # lookup 
        heading_value_1 = self._heading_map[numbered_col_internal]
        heading_value_1_offset = numbered_col_internal

        heading_value_2 = self._heading_map[numbered_col_other_internal]
        heading_value_2_offset = numbered_col_other_internal

        self._heading_map[heading_value_1_offset] = heading_value_2
        self._heading_map[heading_value_2_offset] = heading_value_1


        self.clear()
        self._update_headings()

        debug.dlog(f"now dragging {numbered_col_other}", 2)

        self._stateHolder.transition_swapping(True, numbered_col_other)
        # self._drag_start_column_number=numbered_col_other


        debug.dlog(f"{self._heading_map}")


    def insert(self, *args, **kwargs):
        """map ordering of results to internal ordering"""
        value_list=list(kwargs['values'])
        value_list[2]=value_list[2][:8]
        super().insert('', 'end', values=self._values_reordered(value_list))
        #super().insert('', 'end', values=self._values_reordered(kwargs['values']))

    def clear(self):
        self.delete(*self.get_children())
