from tkinter import ttk
from tkinter import *
from tkinter import font
import enum
from collections import namedtuple
from pprint import pprint, pformat
import debug
import statistics
import bisect
from dataclasses import dataclass
from decimal import Decimal
from functools import reduce

PricingData = namedtuple("PricingData", ["cpu", "env", "start"])
PricingQuintiles = namedtuple("PricingQuintiles", ["cpu", "env", "start"])
PricingSummaries = namedtuple("PricingStats", ["cpu", "env", "start"])

from pathlib import Path
projectdir = Path(__file__).parent.parent

@dataclass
class Pricing:
    pricing: list  # [PricingData]
    cpu: list  # [Decimal]
    env: list  # [Decimal]
    start: list  # [Decimal]
    count: int

    cpuQuintetCounts: list  # [Decimal]
    envQuintetCounts: list  # [Decimal]
    startQuintetCounts: list  # [Decimal]

    def __init__(self, pricing):
        self.pricing = pricing
        self.cpu = [price.cpu for price in self.pricing]
        self.cpu.sort()
        self.env = [price.env for price in self.pricing]
        self.env.sort()
        self.start = [price.start for price in self.pricing]
        self.start.sort()
        self.count = len(pricing)

        def find_counts(prices):
            def find_le(a, x):
                # https://docs.python.org/3/library/bisect.html#searching-sorted-lists
                "Find rightmost value less than or equal to x"
                i = bisect.bisect_right(a, x)
                if i:
                    return a[i - 1]
                raise ValueError

            try:
                quintiles = statistics.quantiles(prices, n=5, method="inclusive")

                quintet = list(
                    map(lambda quintile: find_le(prices, quintile), quintiles)
                )
                counts = list(
                    map(
                        lambda _quintet_: sum(
                            1 for price in prices if price <= _quintet_
                        ),
                        quintet,
                    )
                )
                rv = tuple(zip(quintet, counts))
            except statistics.StatisticsError:  # < 2 data points
                rv = None

            return rv

        self.cpuQuintetCounts = find_counts(self.cpu)
        self.envQuintetCounts = find_counts(self.env)
        self.startQuintetCounts = find_counts(self.start)

        # debug.dlog(f"cpuQuintetCounts: {pformat(self.cpuQuintetCounts)}")
        # debug.dlog(f"envQuintetCounts: {pformat(self.envQuintetCounts)}")
        # debug.dlog(f"startQuintetCounts: {pformat(self.startQuintetCounts)}")
        # debug.dlog(f"max count: {self.count}")
        # debug.dlog(f"len self: {len(self)}")

    def __len__(self):
        return len(self.pricing)


class TreeFrame(ttk.Frame):
    """
    TreeFrame
    --------------
    +glmcounts()
    ...

    """

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
        mem = 11
        storage = 12
        freq=13

    class StateHolder:
        __swapping = False
        __drag_start_column_number = ""
        __inserting = False

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
        def inserting(self):
            return self.__inserting

        @inserting.setter
        def inserting(self, truth_value):
            self.__inserting = truth_value
            if self.__inserting == False:
                debug.dlog("insertion complete")
                self._owner._pricingGlm = Pricing(self._owner._pricingGlmIntermediate)
                self._owner._pricingTglm = Pricing(self._owner._pricingTglmIntermediate)
                if not self._owner.whether_at_least_one_model():
                    # hide the modelinfo column
                    self._owner._headings_invisible.add(self._owner.Field.model)
            else:  # new insertion started
                # del(self._owner._pricingGlm)
                # del(self._owner._pricingTglm)
                self._owner._pricingGlmIntermediate.clear()
                self._owner._pricingTglmIntermediate.clear()

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
        "features",  # 10
        "mem",  # 11
        "storage",  # 12
        "frequency", #13
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
        "'inf.mem'.gib",
        "'inf.storage'.gib",
        "freq"
    )

    _heading_map = [num for num in range(len(_kheadings))]
    _heading_map = [0,1,2,3,4,5,6,7,13,8,9,10,11,12,]
    # e.g. (0, 1, 2, ...)
    _kheadings_init = tuple(
        [str(num) for num in range(len(_kheadings))]
    )  # e.g. ('0', '1', '2', ...)
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
        "features": {},
        "mem": {},
        "storage": {},
    }

    def change_visibility(self, colnum, whetherVisible):
        colnum = int(colnum)
        if not whetherVisible:
            self._headings_invisible.add(colnum)
        else:
            self._headings_invisible.discard(colnum)

    #               CustomTreeView __init__                                  <
    def __init__(self, ctx, root, *args, **kwargs):
        """constructor for CustomTreeView"""
        """post:
            _ctx                :   AppView contextual parent
            _update_cmd_dict    :   callback lookup table

            buttons bound
            column options set
        """
        self.cpuimg = PhotoImage(file=f"{str(projectdir / 'gs/78874_cpu_z_icon.png')}")
        super().__init__(root, *args, **kwargs)
        self.root = root
        #        kwargs["columns"] = self._kheadings_init
        #        self.tree = ttk.Treeview(self, **kwargs)
        # self._headings_invisible = {0, 8, self.Field.model}
        self._headings_invisible = {0, self.Field.model}
        self._separatorDragging = False
        self._stateHolder = self.StateHolder(self)
        # initialize super with columns
        self._ctx = ctx
        # self._update_cmd_dict = self.__build__update_cmd()
        # set mouse button bindings

        # debug.dlog(f"internal columns: {self.tree['columns']}")
        self.last_cleared_selection = list()

        self._pricingGlm = None  # = [] # named tuples of cpu, env, start
        self._pricingTglm = None  # [] # named tuples of cpu, env, start
        self._pricingGlmIntermediate = []
        self._pricingTglmIntermediate = []

        self._make_tree()
        self._update_headings()

    #               CustomTreeView __init__                                  >

    def whether_at_least_one_model(self):
        children = self.tree.get_children()
        last_model_info = reduce(
            lambda a, b: a if a != "" else b,
            [self.tree.item(id)["values"][self.Field.model] for id in children],
        )
        return last_model_info != ""

    def list_selection_addresses(self):
        """extract the node address values from the selection and return
        as a list or empty list"""
        thelist = []
        for item_id in self.tree.selection():
            thelist.append(
                (
                    self.tree.item(item_id)["values"][TreeFrame.Field.offerRowID],
                    self.tree.item(item_id)["values"][TreeFrame.Field.address],
                    self.tree.item(item_id)["values"][TreeFrame.Field.name],
                )
            )
        return thelist

    def get_selected_rowid(self):
        """return the rowid for a singly selected row or None"""
        rowid = None
        sel = self.tree.selection()
        if len(sel) == 1:
            rowid = self.tree.item(sel)["values"][TreeFrame.Field.offerRowID]
        return rowid

    def on_select(self, e=None):
        """update the count selected linked variable unless tree is
        swapping or updating"""
        if not self._stateHolder.whether_swapping() and not self._ctx.whetherUpdating:
            count_selected = len(self.tree.selection())
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

    def _make_tree(self):
        try:
            self.tree.destroy()
        except:
            pass
        self.tree = ttk.Treeview(self, columns=self._kheadings_init)
        self.tree.bind("<Button-1>", self.on_drag_start)
        self.tree.bind("<B1-Motion>", self.on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_release)
        self.tree.bind("<Motion>", self.on_motion)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # hide node, offerRowID columns
        self.tree.column("#0", width=16, stretch=NO)
        self.tree.column("0", width=0, stretch=NO)  # offerRowID

        # setup visible columns
        self.tree.column(1, width=0, anchor="w")
        self.tree.column(2, width=0)
        for index in range(3, len(self._kheadings_init)):
            self.tree.column(index, width=0, anchor="w")

        self.tree.tag_configure("tglm", foreground="red")
        self.tree.grid(column=0, row=0, sticky="news")

        self.s = ttk.Scrollbar(self, orient=VERTICAL, command=self.tree.yview)
        self.s.grid(row=0, column=1, sticky="ns")
        self.tree["yscrollcommand"] = self.s.set

    def _update_headings(self):
        """
        inputs           process                             output
        _kheadings       each _heading_map offset+1          gui headings
        _heading_map     map heading fr _kheadings
        """
        self._make_tree()
        feature_filter = ""
        try:
            if self._ctx.feature_entryframe.whether_checked:
                self.change_visibility(self.Field.features, True)
            else:
                self.change_visibility(self.Field.features, False)
        except:  # kludge
            self.change_visibility(self.Field.features, False)

        def map_heading_from_kheadings(offset, heading_index):
            heading_text = self._kheadings[heading_index]
            stretch = (
                YES if self._heading_map[offset] not in self._headings_invisible else NO
            )
            # debug.dlog(self._headings_invisible)
            if not stretch:
                self.tree.column(offset, stretch=NO, width=0)
            else:
                if self._heading_map[offset] == int(self.Field.model):
                    self.tree.column(offset, stretch=YES, width=190, minwidth=190)
                elif self._heading_map[offset] in [int(self.Field.name)]:
                    self.tree.column(offset, stretch=YES, width=170, minwidth=170)
                elif self._heading_map[offset] == int(self.Field.features):
                    self.tree.column(offset, stretch=YES, width=190, minwidth=190)
                else:
                    self.tree.column(offset, stretch=YES, width=100, minwidth=100)
            self.tree.heading(offset, text=self._kheadings[heading_index], anchor="w")

        # deprecated kludge, need to redraw headings to enforce initial widths...
        # self.grid_remove()
        # self._ctx.treeframe.grid_remove()
        #self.tree.tag_configure('ci', image=self.cpuimg)
        #self.tree.column("#0", tags=('ci'))
        self.tree.heading("#0", image=self.cpuimg)
        for offset, heading_index in enumerate(self._heading_map):
            map_heading_from_kheadings(offset, heading_index)
        # self._ctx.treeframe.grid()
        # self.grid()
        self.tree.update_idletasks()
        # self._ctx.selection_tree.pseudogrid()  # breaks view on mac os x

    def on_drag_start(self, event):
        # update the retained list on pre-emptively kludge TODO review
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
        # self._pricingGlm.clear()
        # self._pricingTglm.clear()
        if not retain_selection:
            self.last_cleared_selection.clear()
        else:
            if len(self.list_selection_addresses()) > 0:  # assume update needed
                self.last_cleared_selection = self.list_selection_addresses()

        children = self.tree.get_children()
        if len(children) > 0:
            self.tree.delete(*children)

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

    def notify_insert_begin(self):
        """informs Tree to expect insertions"""
        self._stateHolder.inserting = True

    def notify_insert_end(self):
        """informs Tree that all insertions have been completed"""
        self._stateHolder.inserting = False

    def insert(self, *args, **kwargs):
        """map ordering of results to internal ordering"""
        # inputs should be values, currency_unit
        # currently the mapping is fixed from what appview has defined for kwargs['values']
        # and it is assumed this will stay constant with TreeFrame.Field BROKEN COUPLING!
        # TODO: consider retaining named tuple form as input
        # or use TreeFrame.Field somehow from appview
        value_list = list(kwargs["values"])
        node_address = value_list[TreeFrame.Field.address] # warning, Field.address not fixed
        value_list[TreeFrame.Field.address] = value_list[TreeFrame.Field.address][:9]
        currency_unit = kwargs["currency_unit"]
        modelname=value_list[9]
        modelfreq=value_list[13]

        pricingData = PricingData(
            value_list[TreeFrame.Field.cpu_per_hr],
            value_list[TreeFrame.Field.dur_per_hr],
            value_list[TreeFrame.Field.start],
        )
        if currency_unit == "glm":
            self._pricingGlmIntermediate.append(pricingData)
            tags = tuple()
        else:
            self._pricingTglmIntermediate.append(pricingData)
            tags = ("tglm",)

        inserted = self.tree.insert(
            "",
            "end",
            values=self._values_reordered(value_list),
            iid=node_address,
            tags=tags,
            image='' if modelname == '' else self.cpuimg,
        )
        # debug.dlog(kwargs)
        # item_inserted = self.tree.item(inserted)
        # item_inserted['image']=self.cpuimg


    def get_heading(self, index):
        """return the heading name currently at the specified index"""
        # for now just using self.heading(index)['text']
        return self.tree.heading(index)["text"]

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def glmcounts(self, reverse=False):
        """return the number of rows corresponding to glm and tglm as a pair"""
        if not reverse:
            return (
                len(self._pricingGlm),
                len(self._pricingTglm),
            )
        else:
            return (
                len(self._pricingTglm),
                len(self._pricingGlm),
            )

    def numerical_summary(self, tglm=False):
        if not tglm:
            pricing = self._pricingGlm
        else:
            pricing = self._pricingTglm
        try:
            pricingStats = PricingSummaries(
                cpu=(
                    min(pricing.cpu),
                    *pricing.cpuQuintetCounts,
                    max(pricing.cpu),
                ),
                env=(
                    min(pricing.env),
                    *pricing.envQuintetCounts,
                    max(pricing.env),
                ),
                start=(
                    min(pricing.start),
                    *pricing.startQuintetCounts,
                    max(pricing.start),
                ),
            )
        except:
            pricingStats = None
        return pricingStats
