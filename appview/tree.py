from tkinter import ttk
from tkinter import *
from tkinter import font
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
        offerRowID = 0
        name = 1
        address = 2
        cpu_per_hr = 3
        dur_per_hr = 4
        start = 5
        cores = 6
        threads = 7
        version = 8
        model = 9
        features = 10

    class StateHolder:
        __swapping = False
        __drag_start_column_number = ""

        def __init__(self, owner):
            self._owner = owner

        def whether_swapping(self):
            """indicates if a column has been dragged out of its
            last place"""
            return self.__swapping

        def transition_swapping(self, truthy: bool, drag_from=""):
            if not truthy:
                self.__drag_start_column_number = ""
            else:
                assert drag_from != "", (
                    "expected a column number if" " swapping state being updated"
                )
                self.__drag_start_column_number = drag_from
            self.__swapping = truthy

        @property
        def drag_start_column_number(self):
            # assert self.__swapping==True, "no column being dragged" \
            #        " but queried for start"
            return self.__drag_start_column_number

        @drag_start_column_number.setter
        def drag_start_column_number(self, colstr: str):
            assert isinstance(colstr, str), "colstr input as non-string"
            debug.dlog(colstr)
            self.__drag_start_column_number = colstr

    _kheadings = (
        "offerRowID",  # 0
        "name",  # 1
        "address",  # 2
        "cpu (/hr)",  # 3
        "duration (/hr)",  # 4
        "start",  # 5
        "cores",  # 6
        "threads",  # 7
        "version",  # 8
        "modelname",  # 9
        "features",
    )

    _kheadings_sql_paths = (
        None,
        "'node.id'.name",
        "'offers'.address",
        "'com.pricing.model.linear.coeffs'.cpu_sec",
        "'com.pricing.model.linear.coeffs'.duration_sec",
        "'com.pricing.model.linear.coeffs'.fixed",
        "'inf.cpu'.cores",
        "'inf.cpu'.threads",
        "'runtime'.version",
        "modelname",
        "filteredFeatures",
    )

    _heading_map = [num for num in range(len(_kheadings))]
    # e.g. (0, 1, 2, ...)
    _kheadings_init = tuple(
        [str(num) for num in range(len(_kheadings))]
    )  # e.g. ('0', '1', '2', ...)

    _headings_invisible = {0, 8}

    #    _kupdate_cmds=[ {}, {"sort_on": "'node.id'.name"}
    # , {"sort_on": "'offers'.address"}, {}, {}
    _update_cmd_dict = {
        "name": {"sort_on": "'node.id'.name"},
        "address": {"sort_on": "'offers'.address"},
        "cpu (/hr)": {},
        "duration (/hr)": {},
        "start": {},
        "cores": {},
        "threads": {},
        "version": {},
        "modelname": {},
        "features": {}
    }

    def change_visibility(self, colnum, whetherVisible):
        colnum = int(colnum)
        if not whetherVisible:
            self._headings_invisible.add(colnum)
        else:
            self._headings_invisible.discard(colnum)

    ####################################################################
    #               CustomTreeView __init__                            #
    ####################################################################
    def __init__(self, ctx, *args, **kwargs):
        """constructor for CustomTreeView"""
        """post:
            _ctx                :   AppView contextual parent
            _update_cmd_dict    :   callback lookup table

            buttons bound
            column options set
        """
        self._separatorDragging = False
        self._stateHolder = self.StateHolder(self)
        # initialize super with columns
        kwargs["columns"] = self._kheadings_init
        super().__init__(*args, **kwargs)
        self._ctx = ctx
        # self._update_cmd_dict = self.__build__update_cmd()
        # set mouse button bindings
        self.bind("<Button-1>", self.on_drag_start)
        self.bind("<B1-Motion>", self.on_drag_motion)
        self.bind("<ButtonRelease-1>", self.on_drag_release)
        self.bind("<Motion>", self.on_motion)
        self.bind("<<TreeviewSelect>>", self.on_select)

        # hide node, offerRowID columns
        self.column("#0", width=0, stretch=NO)
        self.column("0", width=0, stretch=NO)  # offerRowID
        # setup visible columns
        self.column(1, width=0, anchor="w")
        self.column(2, width=0)
        for index in range(3, len(self._kheadings_init)):
            self.column(index, width=0, anchor="w")
        # debug.dlog(f"internal columns: {self['columns']}")
        self.last_cleared_selection = list()

        # self._update_headings()

        self.s = ttk.Scrollbar(self._ctx.treeframe, orient=VERTICAL, command=self.yview)
        self.s.grid(row=0, column=1, sticky="ns")
        self["yscrollcommand"] = self.s.set
        self.tag_configure("tglm", foreground="red")

    def list_selection_addresses(self):
        """extract the node address values from the selection and return
        as a list or empty list"""
        thelist = []
        for item_id in self.selection():
            thelist.append(
                (
                    self.item(item_id)["values"][CustomTreeview.Field.offerRowID],
                    self.item(item_id)["values"][CustomTreeview.Field.address],
                    self.item(item_id)["values"][CustomTreeview.Field.name],
                )
            )
            # print(self.item(item_id)['values'])
        return thelist

    def get_selected_rowid(self):
        """return the rowid for a singly selected row or None"""
        rowid = None
        sel = self.selection()
        if len(sel) == 1:
            rowid = self.item(sel)["values"][CustomTreeview.Field.offerRowID]
        return rowid

    def on_select(self, e=None):
        """update the count selected linked variable unless tree is
        swapping or updating"""
        if not self._stateHolder.whether_swapping() and not self._ctx.whetherUpdating:
            count_selected = len(self.selection())
            if count_selected == 1:
                self._ctx.cursorOfferRowID = self.get_selected_rowid()
            else:
                self._ctx.cursorOfferRowID = None

            # debug.dlog(self.list_selection_addresses())
            self._ctx.count_selected = count_selected
            if count_selected != 0:
                self._ctx.on_select()
            else:
                self._ctx.on_none_selected()

    def _model_sequence_from_headings(self):
        """follow the order of the headings to return a tuple of strings
        corresponding to the model table.column addresses"""
        """analysis
        the current ordering is found in self._heading_map, which lists
        pointer indices. _kheadings_sql_paths contain the sql path at the
        corresponding indices. we are not interested at this time in
        anything before 'cpu (/hr)', so we start at index 3
        """
        t = ()
        for index in range(3, len(self._heading_map)):
            heading_index = self._heading_map[index]
            sql_path = self._kheadings_sql_paths[heading_index]
            if sql_path == "modelname":
                sql_path = "freq"  # kludge
            t += (sql_path,)
            # debug.dlog(t)
        return t

    def _update_headings(self):
        """
        inputs           process                             output
        _kheadings       each _heading_map offset+1          gui headings
        _heading_map     map heading fr _kheadings
        """
        feature_filter=''
        debug.dlog(f"----->{self._ctx.feature_entryframe.cbFeatureEntryVar.get()}")
        if self._ctx.feature_entryframe.cbFeatureEntryVar.get() == "feature":
            feature_filter=self._ctx.featureEntryVar.get()
            self.change_visibility(10, True)
        else:
            self.change_visibility(10, False)

        self.grid_remove()
        self._ctx.treeframe.grid_remove()
        for offset, heading_index in enumerate(self._heading_map):
            heading_text = self._kheadings[heading_index]
            stretch = YES if self._heading_map[offset] not in self._headings_invisible else NO
            debug.dlog(self._headings_invisible)
            if not stretch:
                self.column(offset, stretch=NO, width=0)
            else:
                if self._heading_map[offset] == int(self.Field.model):
                    self.column(offset, stretch=YES, width=200)
                elif self._heading_map[offset] == int(self.Field.name):
                    self.column(offset, stretch=YES, width=75)
                elif self._heading_map[offset] == int(self.Field.features):
                    self.column(offset, stretch=YES, width=150)
                else:
                    self.column(offset, stretch=YES, width=0)
            self.heading(offset, text=self._kheadings[heading_index], anchor="w")
        self._ctx.treeframe.grid()
        self.grid()
        self.update_idletasks()

    def on_drag_start(self, event):
        # update the retained list on pre-emptively kludge TODO review
        # if len(self.list_selection_addresses()) > 0:
        #     debug.dlog(f"replacing {self.last_cleared_selection}" \
        # + " with {self.list_selection_addresses()}")
        #     self.last_cleared_selection = self.list_selection_addresses()
        self.last_cleared_selection = self.list_selection_addresses()

        widget = event.widget
        region = widget.identify_region(event.x, event.y)
        if region == "heading":
            widget._drag_start_x = event.x
            widget._drag_start_y = event.y
            self._stateHolder.drag_start_column_number = widget.identify_column(event.x)
        elif region == "separator":
            self._separatorDragging = True
            return "break"
        else:
            self._stateHolder.transition_swapping(False)  # review

    def on_motion(self, event):
        widget = event.widget
        region = widget.identify_region(event.x, event.y)
        hover_col = widget.identify_column(event.x)
        if region == "separator":
            return "break"

    def on_drag_motion(self, event):
        """swap columns when moved into a new column (except where
        restricted)"""

        if self._separatorDragging == True:
            return

        widget = event.widget
        region = widget.identify_region(event.x, event.y)
        hover_col = widget.identify_column(event.x)

        if region == "heading":
            if not self._stateHolder.whether_swapping():
                if (
                    hover_col not in ("#2", "#3")
                    and hover_col != self._stateHolder.drag_start_column_number
                ):
                    self._stateHolder.transition_swapping(
                        True, self._stateHolder.drag_start_column_number
                    )
            elif self._stateHolder.whether_swapping():
                if hover_col not in (
                    "#2",
                    "#3",
                ) and self._stateHolder.drag_start_column_number not in ("#2", "#3"):
                    # debug.dlog(f"start: "
                    # f"{self._stateHolder.drag_start_column_number}"
                    # f"; hover_col: {hover_col}")
                    if self._stateHolder.drag_start_column_number != hover_col:
                        self._swap_numbered_columns(
                            self._stateHolder.drag_start_column_number, hover_col
                        )

    def on_drag_release(self, event):
        """update display when a column has been moved (assumed
        non-movable columns not moved)"""
        if self._separatorDragging == True:
            self._separatorDragging = False
            return

        # debug.dlog(f"selected address: {self.list_selection_addresses()}")
        widget = event.widget
        region = widget.identify_region(event.x, event.y)
        if region == "heading":
            curcol = widget.identify_column(event.x)
            # debug.dlog(f"curcol: {curcol}; drag_start: {self._stateHolder.drag_start_column_number}")
            if self._stateHolder.whether_swapping():
                # [ column was being dragged ]
                self._ctx._update_cmd()
                # if curcol not in ("#2", "#3"):
                # self._ctx._update_cmd()
            elif curcol == self._stateHolder.drag_start_column_number:
                # [mouse click began and end on same column]
                # [ on non movable #2 ]
                if curcol == "#2":
                    self._ctx._update_cmd(self._update_cmd_dict["name"])
                # [ on non movable #3 ]
                elif curcol == "#3":
                    self._ctx._update_cmd(self._update_cmd_dict["address"])
                # [ on a column that could have been moved ]
                else:
                    cmd = {"sort_on": "all"}
                    self._ctx._update_cmd(cmd)
        elif region == "separator":
            return "break"
        elif self._stateHolder.whether_swapping():
            self._ctx._update_cmd()

        self._stateHolder.transition_swapping(False)
        # self._separatorDragging = False

    def clearit(self, retain_selection=False):
        if not retain_selection:
            # debug.dlog(f"replacing {self.last_cleared_selection} with {self.list_selection_addresses()}")
            # self.last_cleared_selection = self.list_selection_addresses()
            debug.dlog("CLEARING SELECTION")
            self.last_cleared_selection.clear()
        else:
            if len(self.list_selection_addresses()) > 0:  # assume update needed
                debug.dlog(
                    f"replacing last_cleared_selection {self.last_cleared_selection} with {self.list_selection_addresses()}"
                )
                self.last_cleared_selection = self.list_selection_addresses()

        children = self.get_children()
        if len(children) > 0:
            self.delete(*children)

    def _values_reordered(self, values):
        """convert the standard values sequence into the internal sequence and return"""
        # debug.dlog(values,3)
        l = [None for _ in self._heading_map]
        for idx, value in enumerate(values):
            newoffset = self._heading_map.index(idx)
            l[newoffset] = value
        return tuple(l)

    def _swap_numbered_columns(self, numbered_col, numbered_col_other):
        """reorder _heading_map based on inputs that came from .identify_column on drag event
        note: does not change contents of underlying rows, if any
        """
        # debug.dlog(f"swapping {numbered_col} with {numbered_col_other}")
        # convert to heading offset
        numbered_col_internal = int(numbered_col[1:]) - 1
        numbered_col_other_internal = int(numbered_col_other[1:]) - 1

        # lookup
        heading_value_1 = self._heading_map[numbered_col_internal]
        heading_value_1_offset = numbered_col_internal

        debug.dlog(self._heading_map)
        heading_value_2 = self._heading_map[numbered_col_other_internal]
        heading_value_2_offset = numbered_col_other_internal

        self._heading_map[heading_value_1_offset] = heading_value_2
        self._heading_map[heading_value_2_offset] = heading_value_1

        self.clearit(retain_selection=True)  # seems repetitive
        self._update_headings()

        self._stateHolder.transition_swapping(True, numbered_col_other)

    def insert(self, *args, **kwargs):
        """map ordering of results to internal ordering"""
        value_list = list(kwargs["values"])
        node_address = value_list[CustomTreeview.Field.address]
        value_list[CustomTreeview.Field.address] = value_list[2][:9]
        # currency_unit=value_list[-1]
        currency_unit = kwargs["currency_unit"]
        if currency_unit == "glm":
            super().insert(
                "", "end", values=self._values_reordered(value_list), iid=node_address
            )
        else:
            super().insert(
                "",
                "end",
                values=self._values_reordered(value_list),
                iid=node_address,
                tags=("tglm"),
            )
        # super().insert('', 'end', values=self._values_reordered(kwargs['values']))

    def get_heading(self, index):
        """return the heading name currently at the specified index"""
        # for now just using self.heading(index)['text']
        return self.heading(index)["text"]

    def clear(self):
        self.delete(*self.get_children())
