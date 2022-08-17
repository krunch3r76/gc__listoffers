"""The application/controller class for gc__listoffers"""
import tkinter as tk
from tkinter import ttk
from . models import Variables
from . views import ClassicView
from . models import OfferLookup
from . models.localconnection import LocalConnection
import multiprocessing

class Application(tk.Tk):
    """Application root window"""

    def select_rows(self):
        """build a sql select statement when either update or refreshing
        and return text"""
        feature_filter = ""

        # if feature filter
        if False:
            feature_filter = self.feature_entryframe.entryVar.get()

        ss = """
            select 'node.id'.offerRowID
            , 'node.id'.name
            , 'offers'.address
            , 'com.pricing.model.linear.coeffs'.cpu_sec
            , 'com.pricing.model.linear.coeffs'.duration_sec
            , 'com.pricing.model.linear.coeffs'.fixed
            , 'inf.cpu'.cores
            , 'inf.cpu'.threads
            , 'runtime'.version
            , MAX('offers'.ts)
            , (select 'runtime'.version FROM 'runtime'
                ORDER BY 'runtime'.version DESC LIMIT 1) AS mv
            , 'inf.cpu'.brand AS modelname
            , (SELECT grep_freq('inf.cpu'.brand)
            ) AS freq
            , 'com.payment.platform'.kind
            ,(
                SELECT json_group_array(value) FROM
                ( SELECT value FROM json_each('inf.cpu'.[capabilities])
                WHERE json_each.value LIKE '%{feature_filter}%'
                )
             ) AS filteredFeatures
            , ROUND('inf.mem'.gib,2)
            , ROUND('inf.storage'.gib,2)
            FROM 'node.id'"
            JOIN 'offers' USING (offerRowID)
            JOIN 'com.pricing.model.linear.coeffs' USING (offerRowID)
            JOIN 'runtime'  USING (offerRowID)
            JOIN 'inf.cpu' USING (offerRowID)
            JOIN 'com.payment.platform' USING (offerRowID)
            JOIN 'inf.mem' USING (offerRowID)
            JOIN 'inf.storage' USING (offerRowID)
            WHERE 'runtime'.name = 'vm'
        )
        """

        # check for lastversion
        if False:
            ss += " AND 'runtime'.version = mv"

        epsilon = "0.000000001"

        def from_secs(decstr):
            epsilonized = Decimal(decstr) / Decimal("3600.0")
            return epsilonized

        # check cpusec filters
        # if (
        #     self.cpusec_entryframe.whether_checked
        #     and self.cpusec_entryframe.entryVar.get()
        # ):
        # if False:
        #     cpu_per_sec = from_secs(self.cpusec_entryframe.entryVar.get())
        #     ss += (
        #         f" AND 'com.pricing.model.linear.coeffs'.cpu_sec - {cpu_per_sec}"
        #         f" <=  {epsilon}"
        #     )
            # ss += f" AND ('com.pricing.model.linear.coeffs'.cpu_sec - {cpu_per_sec}) > 0.00001"
            # ss += f" AND 'com.pricing.model.linear.coeffs'.cpu_sec <= " f"'{cpu_per_sec}'"

        # check duration sec filters
        # if (
        #     self.dursec_entryframe.whether_checked
        #     and self.dursec_entryframe.entryVar.get()
        # ):
        # if False:
        #     duration_per_sec = from_secs(self.dursec_entryframe.entryVar.get())
        #     ss += (
        #         f" AND 'com.pricing.model.linear.coeffs'.duration_sec "
        #         f" - {duration_per_sec} < {epsilon}"
        #     )

        # check start filter
        # if (
        #     self.start_entryframe.whether_checked
        #     and self.start_entryframe.entryVar.get()
        # ):
        #     start_fee_max = float(self.start_entryframe.entryVar.get())
        #     ss += f" AND 'com.pricing.model.linear.coeffs'.fixed <= {start_fee_max}"

        # f/u check feature
        # if (
        #     self.feature_entryframe.whether_checked
        #     and self.feature_entryframe.entryVar.get()
        # ):
        #     ss += ""
        #     ss += f"""
        #          AND json_array_length(filteredFeatures) > 0
        #         """

        # implement ordering logic
        # if self.order_by_last:
        #     ss += " GROUP BY 'offers'.address"
        #     ss += f" ORDER BY {self.order_by_last}"
        #     ss += " COLLATE NOCASE"
        #     pass
        # else:
        #     path_tuple = self.treeframe._model_sequence_from_headings()
        #     ss += " GROUP BY 'offers'.address"
        #     ss += " ORDER BY "
        #     for i in range(len(path_tuple) - 1):
        #         ss += f"{path_tuple[i]}, "
        #     ss += f"{path_tuple[len(path_tuple)-1]}"
        #     ss += " COLLATE NOCASE"

        return ss

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
        self.localConnection = LocalConnection(self.pipe_parent, self.pipe_child, self.offerLookup)
        localConnectionProcess = multiprocessing.Process(target=self.localConnection, daemon=True)
        localConnectionProcess.start()

        # ss=self.select_rows()
        # result = self.offerLookup("1", "devnet-beta", ss, False)
        # print(f"debug ss\n{self.select_rows()}")
        # print(result)
# app = Application()
# app.mainloop()
