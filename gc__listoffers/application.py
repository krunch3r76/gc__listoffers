"""The application/controller class for gc__listoffers"""
import tkinter as tk
from tkinter import ttk
from . models import Variables, SelectionRecord
from . views import ClassicView
from . models import OfferLookup
from . models.localconnection import LocalConnection
import multiprocessing
from . models.sql import select_rows
from debug import logger

"""
temporary notes:
{'id': '0', 'msg': [{'offerRowID': 26, 'name': 'office_10_220', 'address': '0x700e83ffc421d43f95c340774d5816b985fcf804', 'cpu_sec': Decimal('0.0001'), 'duration_sec': Decimal('0.000050'), 'fixed': 0.0, 'cores': 4, 'threads': 1, 'version': '0.2.11', "MAX('offers'.ts)": '2022-08-18 02:13:52.325523+02:00', 'highest_version': '0.2.11', 'modelname': 'Intel(R) Core(TM) i7-4790K CPU @ 4.00GHz', 'freq': '4.00GHz', 'kind': 'erc20-goerli-tglm', 'filteredFeatures': '[]', "ROUND('inf.mem'.gib,2)": 4.0, "ROUND('inf.storage'.gib,2)": 20.0}]}
"""

class Application(tk.Tk):
    """Application root window"""

    def on_max_cpu_click(self, event):
        # event.widget.variable determines whether off or on
        self.view.console.write("woo hoo, you activated the max cpu filter entry!")
        self.variables['signals']['new_filter_criteria'].set(True)
        self.activeFilterVariables.add('max_cpu_checkVar')
        pass

    def lookup_offers(self, refresh=True):
        if refresh:
            self.id += 1
            # clear tree
            self.view.clear_provider_tree()
        ss=select_rows()
        pipemsg={ "id": self.id, "msg": { "subnet-tag": "public-beta", "sql": ss } }
        self.pipe_parent.send(pipemsg)
        def _debug_get_rows():
            if self.pipe_parent.poll():
                recv = self.pipe_parent.recv()
                logger.debug("fetched!")
                from pprint import pprint
                # pprint(recv['msg'])
                # sample=recv['msg'][0]
                for sample in recv['msg']:
                    try:
                        sampleNT = SelectionRecord(**dict(sample)) # enforce model and controller agree
                    except:
                        pass
                    else:
                        self.view.insert_provider_row(sampleNT._asdict())
                    # pprint(sampleNT._asdict()) # back to dictionary to send over to view, also will enforce
                self.view.insert_provider_row(None, last=True)

            else:
                self.after(2, lambda: _debug_get_rows())
                print(".", end="", flush=True)

        logger.debug("fetching from stats")
        _debug_get_rows()

    def _refresh_update_button(self, *args):
        self.variables['signals']['new_filter_criteria'].set(False)
        self.view.widgets['updateButton'].configure(state=tk.NORMAL)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 1
        self.activeFilterVariables = set()

        from pathlib import Path
        projectdir = Path(__file__).parent.parent
        # self.tk.call(
        #     "source", str(projectdir / "forest-ttk-theme/forest-light.tcl")
        # )

        self.tk.call(
            "source", str(projectdir / "Sun-Valley-ttk-theme/sun-valley.tcl")
        )
        s=ttk.Style()
        # s.theme_use("forest-light")
        self.tk.call("set_theme", "sun-valley")
        self.variables = Variables()
        self.title("testing widgets")
        self.bind("<<Clicked Max CPU>>", self.on_max_cpu_click)
        self.bind("<<Clicked Refresh>>", lambda e: self.lookup_offers())
        self.variables['signals']['new_filter_criteria'].trace_add('write', self._refresh_update_button)

        self.view = ClassicView(self, self.variables)
        self.view.grid(sticky="news")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.offerLookup = OfferLookup()
        self.pipe_parent, self.pipe_child = multiprocessing.Pipe()
        self.localConnection = LocalConnection(self.pipe_child, self.offerLookup)
        self.localConnectionProcess = multiprocessing.Process(target=self.localConnection, daemon=False)
        self.localConnectionProcess.start()


        # result = self.offerLookup("1", "devnet-beta", ss, False)
        # print(f"debug ss\n{self.select_rows()}")
        # print(result)
# app = Application()
# app.mainloop()
