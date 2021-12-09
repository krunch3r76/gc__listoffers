


# appview.py
import multiprocessing
from multiprocessing import Process, Queue
import itertools

from tkinter import *
from tkinter import ttk
from tkinter import font

from datetime import datetime
import decimal
from decimal import Decimal
import json
import debug
import subprocess
import platform

from . broca import fetch_new_dialog

if platform.system()=='Windows':
    import winsound


import os

from .frames import *

DIC411="#003366"
DIC544="#4D4D4D"

class CustomTreeview(ttk.Treeview):
    """notes:
        #2 refers to the first column, which is always name
        #3 refers to the second column, which is always address
        the rest are variable
        summary: subtract 1 to get the corresponding index
    """
    # note, the first offset is the rownum
    _heading_map = [ 0, 1, 2, 3, 4, 5, 6, 7, 8 ]
    _kheadings = ('offerRowID', 'name','address','cpu (/sec)', 'duration (/sec)', 'fixed', 'cores', 'threads', 'version')
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
    _drag_start_column_number = None
    _order_by_other = False

    def __init__update_cmd(self):
        self._update_cmd_dict={
            "name": {"sort_on": "'node.id'.name"}
            , "address": {"sort_on": "'offers'.address"}
            , "cpu (/sec)": {}
            , "duration (/sec)": {}
            , "fixed": {}
            , "cores": {}
            , "threads": {}
            , 'version': {}
                }


    def __init__(self, ctx, *args, **kwargs):
        self._ctx = ctx
        self.__init__update_cmd()
        kwargs['columns']=self._kheadings_init
        super().__init__(*args, **kwargs)
        self.bind("<Button-1>", self.on_drag_start)
        self.bind("<B1-Motion>", self.on_drag_motion)
        self.bind("<ButtonRelease-1>", self.on_drag_release)

        self.column('#0', width=0, stretch=NO)
        self.column('0', width=0, stretch=NO) # offerRowID
        for index in range(1,len(self._kheadings_init)):
            self.column(index, width=0, anchor='w')
        # debug.dlog(f"internal columns: {self['columns']}")
        self._update_headings()

    def _model_sequence_from_headings(self):
        """follow the order of the headings to return a tuple of strings corresponding to the model table.column addresses"""
        """analysis
        the current ordering is found in self._heading_map, which lists pointer indices
        _kheadings_sql_paths contain the sql path at the corresponding indices
        we are not interested at this time in anything before 'cpu (/sec)', so we start at index 3
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
                    )



    def on_drag_start(self, event):
        w = event.widget
        region = w.identify_region(event.x, event.y)
        # debug.dlog(region, 2)
        if region == "heading":
            w._drag_start_x=event.x
            w._drag_start_y=event.y
            self._drag_start_column_number=w.identify_column(event.x)
        else:
            self._drag_start_column_number=None


    def on_drag_motion(self, event):
        """swap columns when moved into a new column (except where restricted)"""
        widget = event.widget
        region = widget.identify_region(event.x, event.y)
        # debug.dlog(region, 3)
        if region == "heading":
        # x = widget.winfo_x() - widget._drag_start_x + event.x
        # y = widget.winfo_y() - widget._drag_start_y + event.y
            if self._drag_start_column_number:
               
                drag_motion_column_number = widget.identify_column(event.x)
                if drag_motion_column_number not in ("#2", "#3") and self._drag_start_column_number not in ("#2", "#3"):
                    if self._drag_start_column_number != drag_motion_column_number:
                        self._swap_numbered_columns(self._drag_start_column_number, drag_motion_column_number)


    def on_drag_release(self, event):
        """update display when a column has been moved (assumed non-movable columns not moved)"""
        widget = event.widget
        region = widget.identify_region(event.x, event.y)
        # debug.dlog(region, 2)
        if region == "heading":
        # x = widget.winfo_x() - widget._drag_start_x + event.x
        # y = widget.winfo_y() - widget._drag_start_y + event.y

            curcol=widget.identify_column(event.x)
            if self._drag_start_column_number not in ("#2", "#3") and curcol not in ("#2", "#3"): # kludgey
                self._ctx._update_cmd()
            elif self._drag_start_column_number == curcol:
                if curcol=="#2":
                    self._ctx._update_cmd(self._update_cmd_dict['name'])
                else:
                    self._ctx._update_cmd(self._update_cmd_dict['address'])



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

        """
        heading_idx_col = self._heading_map.index(numbered_col_internal)
        heading_idx_col_other = self._heading_map.index(numbered_col_other_internal)

        debug.dlog(f"heading_idx_col: {heading_idx_col}, heading_idx_col_others: {heading_idx_col_other}")
        heading_map_copy=self._heading_map.copy()
        self._heading_map[heading_idx_col_other]=heading_map_copy[heading_idx_col]
        self._heading_map[heading_idx_col]=heading_map_copy[heading_idx_col_other]
        """

        self.clear()
        self._update_headings()

        debug.dlog(f"now dragging {numbered_col_other}")

        self._drag_start_column_number=numbered_col_other


        debug.dlog(f"{self._heading_map}")


    def insert(self, *args, **kwargs):
        """map ordering of results to internal ordering"""
        super().insert('', 'end', values=self._values_reordered(kwargs['values']))

    def clear(self):
        self.delete(*self.get_children())


class AppView:

    def add_text_over_time_to_label(self, label, text, end, current=0, time=25, newmsg=True):
        if end == 0:
            label['text']=''
            return

        if newmsg:
            label['text']=''
            newmsg=False
            
        label['text']+=text[current]
        current+=1
        add_time=0
        if current != end:
            if text[current-1] == '.':
                add_time=time*15
            elif text[current-1] == ',':
                add_time=time*10
            self.root.after(time+add_time, lambda: self.add_text_over_time_to_label(label, text, end, current, time, newmsg) )

    cancel_current_displayed_message = False
    message_being_displayed = False



    #############################################################################
    #               the mother of all class methods                             #
    #############################################################################
    def __init__(self):
        self.refreshFrame = None
        # message queues used by controller to interface with this
        self.q_out=Queue()
        self.q_in=Queue()

        self.session_id=None    # timestamp of last refresh
        self.order_by_last="'node.id'.name" # current column to sort results on
        # root Tk window and styling
        self.root=Tk()
        self.root.geometry('924x580+100+200')
        s = ttk.Style()
        self.root.tk.call('source', './forest-ttk-theme/forest-light.tcl')
        s.theme_use('forest-light')

        # setup widgets and their linked variables
        self.cpusec_entry_var = StringVar(value='0.1')
        self.durationsec_entry_var = StringVar(value='0.02')
        self.subnet_var = StringVar()
        self.other_entry_var = StringVar()
        # countlabel
        self.resultcount_var = StringVar(value="0")
        # countdifflabel
        self.resultdiffcount_var = StringVar(value="")
        self.session_resultcount = 0 # stores the number of rows currently on the table
        self.lastresultcount = 0 # temporary to store the displayed result number count before refresh
        self.cursorOfferRowID = None # stores the RowID of a selected row
        decimal.getcontext().prec=7 # sets the precision of displayed decimal numbers
        self.rawwin = None # a window for displaying raw results
        self.ssp = None # current sound Process/Subprocess instance

        # configure layout
        style=ttk.Style()
        style.configure("Treeview.Heading", foreground=DIC411)

        root=self.root
        root.title("Provider View")
        root.columnconfigure(0, weight=1) # ratio for children to resize against
        root.rowconfigure(0, weight=1) # ratio for children to resize against
        root.rowconfigure(1, weight=0)
        root.rowconfigure(2, weight=0)
        # treeframe
        treeframe = ttk.Frame(root)
        treeframe.columnconfigure(0, weight=1) # resize by same factor as root width
        treeframe.rowconfigure(0, weight=1) # resize by same factor as root height
        treeframe['padding']=(0,0,0,5)
        self.tree = CustomTreeview(self, treeframe)
        treeframe.grid(column=0, row=0, sticky="news")
        self.tree.grid(column=0, row=0, sticky="news")

#        self.tree.columnconfigure(0, weight=1)
#        self.tree.rowconfigure(0, weight=1)

        self.subnet_var.set('public-beta')
        self.other_entry_var.set('devnet-beta.2')
        self.other_entry_var.trace_add("write", self._on_other_entry_change)

        # baseframe
        baseframe = ttk.Frame(root)
        baseframe.grid(column=0, row=1, sticky="wes")
        baseframe.columnconfigure(0, weight=1)
        baseframe.columnconfigure(1, weight=1)
        baseframe.columnconfigure(2, weight=1)
        baseframe.columnconfigure(3, weight=1)
        baseframe.rowconfigure(0, weight=1)

        baseframe['padding']=(0,5,0,10)

        self.refreshFrame       = RefreshFrame(self, self._toggle_refresh_controls_closure(), baseframe)
        self.count_frame        = CountFrame(self, baseframe)
        self.count_frame.w.grid(        column=2, row=0, )

        self.refreshFrame.w['padding']=(0,0,0,0)
        self.refreshFrame.w.grid(       column=1, row=0, sticky="wnes")

        emptyframe_right=ttk.Frame(baseframe)
        emptyframe_right.grid(          column=3, row=0)

        self.l_baseframe=ttk.Frame(baseframe)
        self.l_baseframe.columnconfigure(0, weight=1)
        self.l_baseframe.rowconfigure(0, weight=1)
        self.l_baseframe.grid(          column=0, row=0, sticky='nwes')


        self.label_logo = ttk.Label(emptyframe_right, anchor='center')
        self.fe_image=PhotoImage(file='gs/the_empire_spaceship_and_sun_by_tempest790_db0ww24.png')
        self.fe_image_ico=PhotoImage(file='gs/the_empire_spaceship_and_sun_by_tempest790_db0ww24_48x48.png')

        self.label_logo['image']=self.fe_image
        self.label_logo.grid(column=0, row=0, sticky='wnes')

        self.root.iconphoto(True, self.fe_image_ico)
        # emptyframe_right['borderwidth']=2
        # emptyframe_right['relief']='sunken'


        # setup console with at least 40 characters of width       
        self.console_character_width=40
        self.console = ttk.Label(self.l_baseframe, anchor='nw', width=self.console_character_width)
        self.width_in_font_pixels=self.console_character_width * (font.nametofont('TkDefaultFont').actual()['size']*0.80)
        self.console['wraplength']=self.console_character_width
        self.console.grid(column=0, row=0, sticky='nwes')



        # subbaseframe
        subbaseframe = ttk.Frame(root)
        subbaseframe.grid(column=0, row=2)
        self.cpusec_entryframe  = CPUSecFrame(self, subbaseframe)
        self.dursec_entryframe  = DurSecFrame(self, subbaseframe)

        self.cpusec_entryframe.w.grid(  column=1,row=0, sticky="w")
        self.dursec_entryframe.w.grid(  column=2,row=0, sticky="w")

        # bind to method and inspect event widget TODO
        root.bind('<Escape>', lambda e: root.destroy())

        self._rewrite_to_console(fetch_new_dialog(0))

    def _toggle_refresh_controls_closure(self):
        disabled = False
        other_entry_was_enabled = False

        def toggle():
            nonlocal disabled
            nonlocal other_entry_was_enabled
            radio_frame=self.refreshFrame.radio_frame
            refreshFrame=self.refreshFrame
            if not disabled:
                refreshFrame.refreshButton.state(['disabled'])
                radio_frame.publicbeta_rb.state(['disabled'])
                radio_frame.publicdevnet_rb.state(['disabled'])
                if radio_frame.other_entry.instate(['!disabled']):
                    other_entry_was_enabled = True
                radio_frame.other_rb.state(['disabled'])
                radio_frame.other_entry.state(['disabled'])
                disabled=True
            else:
                refreshFrame.refreshButton.state(['!disabled'])
                radio_frame.publicbeta_rb.state(['!disabled'])
                radio_frame.publicdevnet_rb.state(['!disabled'])
                radio_frame.other_rb.state(['!disabled'])
                if other_entry_was_enabled:
                    radio_frame.other_entry.state(['!disabled'])
                disabled=False

        return toggle





    def _on_offer_text_selection(self, *args):
        e=args[0]
        selection_range=e.widget.tag_ranges('sel')
        if selection_range:
            selection = e.widget.get(*selection_range)
            self.root.clipboard_clear()
            self.root.clipboard_append(selection)




    def _on_other_entry_change(self, *args):
        self.other_rb['value']= self.other_entry_var.get()
        self.subnet_var.set( self.other_entry_var.get() )




    def _on_other_entry_focusout(self, *args):
        subnet=self.subnet_var.get()
        if subnet != 'public-beta' and subnet != 'devnet-beta':
            self.refreshFrame.radio_frame.other_entry.state(['disabled'])



    def _on_other_entry_click(self, *args):
        radio_frame=self.refreshFrame.radio_frame
        if radio_frame.other_rb.instate(['!disabled']):
            subnet=self.subnet_var.get()
            if subnet != 'public-beta' and subnet != 'devnet-beta':
                self.refreshFrame.radio_frame.other_entry.state(['!disabled'])



    def _on_other_radio(self, *args):
        self.refreshFrame.radio_frame.other_entry.state(['!disabled'])
        # debug.dlog(self.other_entry_var.get() )
        self.refreshFrame.radio_frame.other_rb['value']= self.other_entry_var.get()
        self.subnet_var.set( self.other_entry_var.get() )



    def _show_raw(self, *args):
        ss = f"select json from extra WHERE offerRowID = {self.cursorOfferRowID}"
        # review the need to pass subnet-tag on update TODO
        self.q_out.put_nowait({ "id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} })

        results=None
        msg_in = None
        # uh oh, another nested event loop. terminator assigned!
        self.root.after(1, lambda: self.handle_incoming_result_extra())


    def handle_incoming_result_extra(self):
        try:
            msg_in = self.q_in.get_nowait()
        except multiprocessing.queues.Empty:
            msg_in = None
            self.root.after(1, lambda: self.handle_incoming_result_extra())
        else:
            # print(f"[AppView] got msg!")
            results = msg_in["msg"]
            # print(msg_in["id"])

            results_json = json.loads(results[0][0])
            props=results_json["props"]
            props_s = json.dumps(props, indent=5)
            # create/replace a new window
            self.rawwin = Toplevel(self.root)        
            self.rawwin.columnconfigure(0, weight=1)
            self.rawwin.rowconfigure(0, weight=1)

            f = ttk.Frame(self.rawwin)
            f.grid(column=0, row=0, sticky="news")
            f.columnconfigure(0, weight=1)
            f.rowconfigure(0, weight=1)
            txt = Text(f)
            txt.grid(column=0, row=0, sticky="news")
            txt.insert('1.0', props_s)
            txt.configure(state='disabled')
            txt.bind('<<Selection>>', self._on_offer_text_selection)






    def _update(self, results, refresh=True):
        """update gui with the input results
        called by: handle_incoming_result
        """
        if refresh:
            self.session_resultcount=len(results)

        for result in results:
            result=list(result)
            self.tree.insert('', 'end', values=(result[0], result[1], result[2], Decimal(result[3])*Decimal(3600.0), Decimal(result[4])*Decimal(3600.0), result[5], result[6], result[7]))

        current_resultcount=len(results)
        self.resultcount_var.set(str(current_resultcount))
        
        if not refresh:
            disp=""
            if self.lastresultcount != 0 and self.session_resultcount != current_resultcount:
                disp+="/" + str(self.session_resultcount) + "("
                diff =  current_resultcount - self.lastresultcount
                POS=False
                if diff >0:
                    disp+="+"
                disp+=str(current_resultcount - self.lastresultcount) + ")"
                self.resultdiffcount_var.set(disp)
                # self.resultcount_var.set(str(new_resultcount))
            else:
                self.resultdiffcount_var.set("") # consider edge cases

        self.refreshFrame._toggle_refresh_controls()
        if refresh:
            self._rewrite_to_console(fetch_new_dialog(3))
        else:
            self._rewrite_to_console(None)




    def _update_cmd(self, *args):
        """query model for rows on current session_id before handing off control to self.handle_incoming_result"""
        self.refreshFrame._toggle_refresh_controls()

        if self.resultcount_var.get() != "":
            self.lastresultcount=int(self.resultcount_var.get())
        else:
            self.lastresultcount=0

        self.resultcount_var.set("")
        self.resultdiffcount_var.set("")

        self.tree.delete(*self.tree.get_children())
        if not self.session_id:
            return

        if len(args) > 0 and 'sort_on' in args[0]:
            self.order_by_last = args[0]['sort_on']
        else:
            self.order_by_last=None

        ss = self._update_or_refresh_sql()

        # TODO remove subnet-tag, it is already associated with the id
        self.q_out.put_nowait({"id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} })

        results=None
        msg_in = None

        self.root.after(1, lambda: self.handle_incoming_result(refresh=False))






    def _update_or_refresh_sql(self):
        ss = "select 'node.id'.offerRowID, 'node.id'.name, 'offers'.address, 'com.pricing.model.linear.coeffs'.cpu_sec, 'com.pricing.model.linear.coeffs'.duration_sec, 'com.pricing.model.linear.coeffs'.fixed, 'inf.cpu'.cores, 'inf.cpu'.threads, max('offers'.ts)" \
            " FROM 'node.id'" \
            " INNER JOIN 'offers' USING (offerRowID)" \
            " INNER JOIN 'com.pricing.model.linear.coeffs' USING (offerRowID)" \
            " INNER JOIN 'runtime'  USING (offerRowID)" \
            " INNER JOIN 'inf.cpu' USING (offerRowID)" \
            " WHERE 'runtime'.name = 'vm' "

        """
        ss = "select 'node.id'.offerRowID, 'node.id'.name, 'offers'.address, 'com.pricing.model.linear.coeffs'.cpu_sec, 'com.pricing.model.linear.coeffs'.duration_sec, 'com.pricing.model.linear.coeffs'.fixed, 'inf.cpu'.cores, 'inf.cpu'.threads, max('offers'.ts)" \
            " FROM 'offers'" \
            " NATURAL JOIN 'node.id'" \
            " NATURAL JOIN 'com.pricing.model.linear.coeffs'" \
            " NATURAL JOIN 'runtime'" \
            " NATURAL JOIN 'inf.cpu'" \
            " WHERE 'runtime'.name = 'vm' "
        """

        if self.cpusec_entryframe.cpusec_entry.instate(['!disabled']) and self.cpusec_entry_var.get():
            ss+= f" AND 'com.pricing.model.linear.coeffs'.cpu_sec <= {Decimal(self.cpusec_entry_var.get())/Decimal('3600.0')}"
         
        if self.dursec_entryframe.durationsec_entry.instate(['!disabled']) and self.durationsec_entry_var.get():
            ss+= f" AND 'com.pricing.model.linear.coeffs'.duration_sec <= {Decimal(self.durationsec_entry_var.get())/Decimal(3600.0)}"

        # here we build the order by statement

        
        if self.order_by_last:
            ss+=" GROUP BY 'offers'.address"
            ss+=f" ORDER BY {self.order_by_last}"
            ss+=" COLLATE NOCASE"
            pass
        else:
            path_tuple = self.tree._model_sequence_from_headings()
            ss+=" GROUP BY 'offers'.address"
            ss+=" ORDER BY "
            for i in range(len(path_tuple)-1):
                ss+=f"{path_tuple[i]}, "
            ss+=f"{path_tuple[len(path_tuple)-1]}"
            ss+=" COLLATE NOCASE"

        debug.dlog(ss)

        return ss


    def _rewrite_to_console(self, msg):
        self.console.grid_remove()


        self.console = ttk.Label(self.l_baseframe, anchor='nw', width=40)
        self.console.grid(column=0, row=0, sticky='nwes')
        self.root.update()
        self.console_character_width=self.l_baseframe.winfo_width() // font.nametofont('TkDefaultFont').actual()['size']
        self.console['width']=self.console_character_width
        self.console['wraplength']=self.l_baseframe.winfo_width()*0.80
        #self.root.update()

        if msg:
            self.add_text_over_time_to_label(self.console, msg, len(msg))
        else:
            self.add_text_over_time_to_label(self.console, "", 0)



    def _refresh_cmd(self, *args):
        """create a new session and query model before handing off control to self.handle_incoming_result"""
        # describe what's happening to client in console area
        self._rewrite_to_console(fetch_new_dialog(1))
        # disable controls
        self.refreshFrame._toggle_refresh_controls()
        # reset widgets to be refreshed
        self.resultcount_var.set("")
        self.resultdiffcount_var.set("")
        self.tree.delete(*self.tree.get_children())
        self.tree.update_idletasks()
        # build sql statement
        ss = self._update_or_refresh_sql()
        # create new session id (current time)
        self.session_id=str(datetime.now().timestamp())

        # ask controller to query model for results
        msg_out = {"id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} }
        self.q_out.put_nowait({"id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} })

        # wait on reply
        self.root.after(1, self.handle_incoming_result)







    def handle_incoming_result(self, refresh=True):
        """wait for results from model before passing control over to self._update"""
        try:
            msg_in = self.q_in.get_nowait()
        except multiprocessing.queues.Empty:
            # msg_in = None
            if refresh:
                if self.ssp == None:
                    if platform.system()=='Windows':
                        self.ssp=Process(target=winsound.PlaySound, args=('.\\gs\\transformers.wav', winsound.SND_FILENAME), daemon=True)
                        self.ssp.start()
                    elif platform.system()=='Linux':
                        self.ssp=subprocess.Popen(['aplay', 'gs/transformers.wav'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif platform.system()=='Darwin':
                        self.ssp=subprocess.Popen(['afplay', 'gs/transformers.wav'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    if isinstance(self.ssp, subprocess.Popen):
                        try:
                            self.ssp.wait(0.01)
                        except:
                            pass
                        else:
                            self.ssp=None
                    else: # Process
                        if not self.ssp.is_alive():
                            self.ssp = None

            self.root.after(10, lambda: self.handle_incoming_result(refresh))

        else:
            results = msg_in["msg"]
            if len(results) > 1:
                if results[0] == 'error':
                    if results[1]=='invalid api key':
                        self._rewrite_to_console(fetch_new_dialog(4))
                    elif results[1]=='invalid api key server side':
                        self._rewrite_to_console(fetch_new_dialog(6))
                    elif results[1]=='connection refused':
                        self._rewrite_to_console(fetch_new_dialog(7))
                    elif results[1]=='cannot connect to yagna':
                        self._rewrite_to_console(fetch_new_dialog(8))
                    else:
                        self._rewrite_to_console(fetch_new_dialog(5))
                    self.refreshFrame._toggle_refresh_controls()
                else:
                    self._update(results, refresh)







    def _cb_cpusec_checkbutton(self, *args):
        if self.cpusec_entryframe.cpusec_entry.instate(['disabled']):
            self.cpusec_entryframe.cpusec_entry.state(['!disabled'])
        else:
            self.cpusec_entryframe.cpusec_entry.state(['disabled'])
        if self.cpusec_entryframe.cpusec_entry.get():
            self._update_cmd()




    def _cb_durationsec_checkbutton(self, *args):
        if self.dursec_entryframe.durationsec_entry.instate(['disabled']):
            self.dursec_entryframe.durationsec_entry.state(['!disabled'])
        else:
            self.dursec_entryframe.durationsec_entry.state(['disabled'])
        if self.dursec_entryframe.durationsec_entry.get():
            self._update_cmd()





    def __call__(self):

        root = self.root
        # popup menu
        root.option_add('*tearOff', FALSE)
        menu = Menu(root)
        menu.add_command(label='<name>')
        menu.entryconfigure(0, state=DISABLED)
        menu.add_separator()
        menu.add_command(label='view raw', command=self._show_raw)
        menu.add_command(label='exit menu')

        def do_popup(event):
            tree=self.tree
            try:
                # identify the coordinates of tree
                # print(tree.state())
                if 'hover' not in tree.state():
                # if tree.state()[0] != 'hover':
                    return
                region = tree.identify_region(event.x, event.y)
                if region != 'cell':
                    menu.grab_release()
                    return
                # print(f"{tree.item( tree.identify_row(event.y) )['values']}")
                menu.entryconfigure(0, label=tree.item( tree.identify_row(event.y) )['values'][1])
                self.cursorOfferRowID=tree.item( tree.identify_row(event.y) )['values'][0]
                menu.post(event.x_root, event.y_root)
            except IndexError:
                pass
            finally:
                menu.grab_release()
        # root.bind('<ButtonRelease-3>', do_popup )
        if (root.tk.call('tk', 'windowingsystem')=='aqua'):
            root.bind('<2>', do_popup)
            root.bind('<Control-1>', do_popup)
        else:
            root.bind('<3>', do_popup )



        # tree.insert('', 'end', values=('namevalue', 'addressvalue', 'cpuvalue', 'durationvalue', 'fixedvalue'))
        root.mainloop()


