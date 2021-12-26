from tkinter import ttk
from tkinter import *
from tkinter import font
import enum

import debug

class SelectionTreeview(ttk.Treeview):
    """
    notes:
        headings are not displayed by default
    """
    class Field(enum.IntEnum):
        offerRowID=0
        name=1
        address=2

    _kHeadings = ('offerRowId', 'name', 'address')
    _gridinfo = None
    def __init__(self, ctx, *args, **kwargs):
        #kwargs['columns']=self._kHeadings
        super().__init__(*args, **kwargs)
        self._ctx = ctx

        self['columns']=self._kHeadings
        self.column('#0', width=0, stretch=NO)
        self.column(0, width=0, stretch=NO)
        for i in range(1, len(self._kHeadings)):
            self.column(i, width=80, anchor='w', stretch=YES)
            self.heading(i, text=self._kHeadings[i], anchor='w')

        self['show']='tree'

    def regrid(self):
        assert self._gridinfo != None
        self.grid(**self._gridinfo)

    def degrid(self):
        """remove itself from grid but retains grid infomation to regrid()"""
        # self._gridinfo = self.grid_info()
        self.grid_forget()
        # debug.dlog(self.grid_info())

    def pseudogrid(self, **kwargs):
        self._gridinfo = kwargs

    def clearit(self):
        """delete all children of root node"""
        self.delete(*self.get_children())

    def update(self, val_list):
        """replace the list with input values"""
        self.clearit()
        for values in val_list:
            self.insert('', 'end', values=values)
