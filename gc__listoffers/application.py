"""The application/controller class for gc__listoffers"""
import tkinter as tk
from tkinter import ttk
from . models import Variables
from . views import ClassicView

# from widgets.checkbuttonentry import CheckbuttonEntry
# from widgets.mycheckbutton import MyCheckbutton
# from widgets.mybutton import MyButton
# from widgets.subnetradio import SubnetRadio
# from widgets.countsummary import CountSummary
# from widgets.providertree import InsertDict, ProviderTree

class Application(tk.Tk):
    """Application root window"""

    def on_max_cpu_click(self, event):
        # event.widget.variable determines whether off or on
        self.console.write("woo hoo, you activated the max cpu filter entry!")
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

# app = Application()
# app.mainloop()
