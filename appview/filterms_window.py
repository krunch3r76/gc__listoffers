from tkinter import *
from tkinter import ttk
from tkinter import font

import debug

class _SettingsChecker():
    def __init__(self, filterwin):
        self._parent = filterwin

    @property
    def whitelist(self):
        """query if whitelisting requested
        comments: false implies blacklisting
        """
        return self._parent._listTypeVar.get() == 'wl'

    @property
    def blacklist(self):
        """query if blacklisting requested"""
        return self._parent._listTypeVar.get() == 'bl'

    @property
    def valonly(self):
        """query if display is requested to be just the filterms array value"""
        return self._parent._arrayOnlyON.get()


def _buildtext(filterwin, checker):
    """build the text to display according to current settings and return"""
    content = filterwin._get_content()
    if not checker.valonly:
        if checker.whitelist:
            text="export GNPROVIDER=["
        else:
            text="export GNPROVIDER_BL=["
    else:
        text="["

    for addr in content:
        text+=f"'{addr}',"
    text=text[:-1]+']'
    return text

class DisplayWidgetWrapper(Frame):
    """Text widget implementation of Display"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._text = Text(self)
        self._text.grid(column=0, row=0, sticky="news")
        self._text['state']='disabled' # prevent editing

    def get_content(self):
        """get all the text and return"""
        return self._text.get('1.0', 'end')

    def replace_content(self, content):
        """write input content to the display"""
        # clear
        self._text.delete('1.0', 'end')
        # insert
        self._text.insert('end', content)


class DisplayWidget(Text):
    """Text widget implementation of Display"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['state']='disabled' # prevent editing

    def get_content(self):
        """get all the text and return"""
        return self.get('1.0', 'end')

    def replace_content(self, content):
        """write input content to the display"""
        # clear
        self['state']='normal'
        self.delete('1.0', 'end')
        # insert
        self.insert('1.0', content)
        self['state']='disabled'



class FiltermsWindow(Toplevel):
    """
    _content: list of addresses to filter
    _checker: SettingsChecker

    _mainframe
    -------
    _rbWhitelist
    _rbBlacklist
        _listTypeVar {'wl', 'bl'}
    _cbArrayOnly
        _arrayOnlyON
    _wTextDisplay
    _bToFile
    _bToClip

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content = None
        self._settingsChecker = _SettingsChecker(self)
        self.resizable(True, False)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        _mainframe = ttk.Frame(self)
        _mainframe = _mainframe

        _mainframe.rowconfigure(0, weight=1)
#        _mainframe.rowconfigure(1, weight=1)
        _mainframe.rowconfigure(2, weight=1)
        _mainframe.rowconfigure(3, weight=1)
        _mainframe.columnconfigure(0, weight=1)
        _mainframe.columnconfigure(1, weight=1)
        _mainframe.columnconfigure(2, weight=1)

        # list kind radiobuttons
        self._listTypeVar=StringVar()
        self._listTypeVar.set('wl')
        self._rbWhitelist = ttk.Radiobutton(_mainframe, text='whitelist', variable=self._listTypeVar, value='wl', command=self._refresh)
        self._rbBlacklist = ttk.Radiobutton(_mainframe, text='blacklist', variable=self._listTypeVar, value='bl', command=self._refresh)

        # array only checkbutton
        self._arrayOnlyON=IntVar()
        self._cbArrayOnly = ttk.Checkbutton(_mainframe, text='show value only', variable=self._arrayOnlyON, command=self._refresh)

        # display
        self._wTextDisplay = DisplayWidget(_mainframe)

        # storage buttons
        # ttk.Style().configure('C.TButton', foreground='green')
        self._bToFile = ttk.Button(_mainframe, text="send to file", command=self._onToFile)
        self._bToClip = ttk.Button(_mainframe, text="send to clipboard", command=self._onToClip)

        # grid
        self._rbWhitelist.grid( column=0,   row=0,  sticky="nw")
        self._rbBlacklist.grid( column=1,   row=0,  sticky="n")
        self._cbArrayOnly.grid( column=2,   row=0,  sticky="ne")
        self._wTextDisplay.grid(column=0,   row=2,  sticky="news",  columnspan=3,   pady=10, padx=10 )

        # self._bToFile.grid(     column=0,   row=3,  sticky="ws", padx=10, pady=10)
        self._bToClip.grid(     column=2,   row=3,  sticky="es", padx=10, pady=10)

        _mainframe.grid(   column=0,   row=0,  sticky="wnes")
        self.grab_set()

    def set_content(self, newcontent):
        """store raw content then refresh display
        in: a sequence having a first element being a node address
        """
        self._content = [ addr[0] for addr in newcontent ]
        self._refresh()

    def _get_content(self):
        """return the content
        called by helper function _buildtext       
        """
        return self._content

    def _onToFile(self, event):
        """
        cb to _bToFile
        """
        pass

    def _onToClip(self):
        """
        cb to _bToClip
        """
        self.clipboard_clear()
        self.clipboard_append("appended")
        # ttk.Style().configure('Color.TButton', foreground='black')

    def _refresh(self):
        """update display given internal content according to current settings
        """
        text=_buildtext(self, self._settingsChecker)
        self._wTextDisplay.replace_content(text)
        # ttk.Style().configure('C.TButton', foreground='green')
        

