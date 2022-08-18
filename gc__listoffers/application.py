"""The application/controller class for gc__listoffers"""
import tkinter as tk
from tkinter import ttk
from . models import Variables
from . views import ClassicView
from . models import OfferLookup
from . models.localconnection import LocalConnection
import multiprocessing
from . models.sql import select_rows
"""
temporary notes:
{'id': '0', 'msg': [{'offerRowID': 26, 'name': 'office_10_220', 'address': '0x700e83ffc421d43f95c340774d5816b985fcf804', 'cpu_sec': Decimal('0.0001'), 'duration_sec': Decimal('0.000050'), 'fixed': 0.0, 'cores': 4, 'threads': 1, 'version': '0.2.11', "MAX('offers'.ts)": '2022-08-18 02:13:52.325523+02:00', 'highest_version': '0.2.11', 'modelname': 'Intel(R) Core(TM) i7-4790K CPU @ 4.00GHz', 'freq': '4.00GHz', 'kind': 'erc20-goerli-tglm', 'filteredFeatures': '[]', "ROUND('inf.mem'.gib,2)": 4.0, "ROUND('inf.storage'.gib,2)": 20.0}]}


"""

from collections import namedtuple
SelectionColumns = ['offerRowID', 'name', 'address', 'cpu_sec', 'duration_sec', 'fixed', 'cores',
                    'threads', 'version', 'most_recent_timestamp', 'highest_version',
                    'modelname', 'freq', 'token_kind', 'features', 'featuresFiltered',
                    'mem_gib', 'storage_gib'
                    ]
SelectionRecord = namedtuple('SelectionRecord', SelectionColumns)

class Application(tk.Tk):
    """Application root window"""


    def on_max_cpu_click(self, event):
        # event.widget.variable determines whether off or on
        self.view.console.write("woo hoo, you activated the max cpu filter entry!")
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from pathlib import Path
        projectdir = Path(__file__).parent.parent
        self.tk.call(
            "source", str(projectdir / "forest-ttk-theme/forest-light.tcl")
        )
        s=ttk.Style()
        s.theme_use("forest-light")
        self.variables = Variables()
        self.title("testing widgets")
        self.bind("<<Clicked Max CPU>>", self.on_max_cpu_click)
        self.view = ClassicView(self, self.variables)
        self.view.grid(sticky="news")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.offerLookup = OfferLookup()
        self.pipe_parent, self.pipe_child = multiprocessing.Pipe()
        self.localConnection = LocalConnection(self.pipe_child, self.offerLookup)
        self.localConnectionProcess = multiprocessing.Process(target=self.localConnection, daemon=False)
        self.localConnectionProcess.start()
        ss=select_rows()
        pipemsg={ "id": "0", "msg": { "subnet-tag": "devnet-beta", "sql": ss } }
        self.pipe_parent.send(pipemsg)
        def _debug_get_rows():
            if self.pipe_parent.poll():
                recv = self.pipe_parent.recv()
                from pprint import pprint
                pprint(recv['msg'])
                sample=recv['msg'][0]
                sampleNT = SelectionRecord(**dict(sample))
                pprint(sampleNT)
            else:
                self.after(2, lambda: _debug_get_rows())
                print(".", end="", flush=True)

        _debug_get_rows()


        # result = self.offerLookup("1", "devnet-beta", ss, False)
        # print(f"debug ss\n{self.select_rows()}")
        # print(result)
# app = Application()
# app.mainloop()
