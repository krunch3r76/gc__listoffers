


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
if platform.system()=='Windows':
    import winsound


import os

from .frames import *

DIC411="#003366"
DIC544="#4D4D4D"




        




class AppView:

    def add_text_over_time_to_label(self, label, text, end, current=0, time=25, newmsg=True):
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

    display_messages = [
        "greetings. please press refresh to see the providers on the default"
        " subnet, public-beta.\n\n"
        "Note, if you are running golemsp on the same system, you won't"
        " see yourself listed here!"
    ,
        "i am now collecting offers broadcast on the provider network.\n\n" \
        "this may take some time especially if it has been awhile since" \
        " i last checked. also, i do not always get all the offers, so" \
        " if the number seems low, please refresh again."
    ]



    #############################################################################
    #               the mother of all class methods                             #
    #############################################################################
    def __init__(self):
        self.refreshFrame = None
        self.message_being_displayed = False
        # message queues used by controller to interface with this
        self.q_out=Queue()
        self.q_in=Queue()

        self.session_id=None    # timestamp of last refresh
        self.order_by_last="'node.id'.name" # current column to sort results on

        # root Tk window and styling
        self.root=Tk()
        self.root.geometry('1024x480+100+200')
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
        root.rowconfigure(1, weight=1)

        # treeframe
        treeframe = ttk.Frame(root)
        treeframe.columnconfigure(0, weight=1) # resize by same factor as root width
        treeframe.rowconfigure(0, weight=1) # resize by same factor as root height
        treeframe['padding']=(0,0,0,5)
        self.tree = ttk.Treeview(treeframe, columns=('offerRowID', 'name','address','cpu', 'duration', 'fixed', 'cores', 'threads'))
        treeframe.grid(column=0, row=0, sticky="news")
        self.tree.grid(column=0, row=0, sticky="news")


        self.subnet_var.set('public-beta')
        self.other_entry_var.set('devnet-beta.2')
        self.other_entry_var.trace_add("write", self._on_other_entry_change)

        # baseframe
        baseframe = ttk.Frame(root)
        baseframe.grid(column=0, row=1, sticky="wnes")
        baseframe.columnconfigure(0, weight=1)
        baseframe.columnconfigure(1, weight=1)
        baseframe.columnconfigure(2, weight=1)
        baseframe.columnconfigure(3, weight=1)
        baseframe.rowconfigure(0, weight=1)

        baseframe['padding']=(0,5,0,10)

        self.refreshFrame       = RefreshFrame(self, self._toggle_refresh_controls_closure(), baseframe)
        self.count_frame        = CountFrame(self, baseframe)

        # self.refreshFrame.w['borderwidth']=2
        # self.refreshFrame.w['relief']='sunken'
        self.refreshFrame.w['padding']=(0,0,0,0)
        # self.count_frame.w['borderwidth']=2
        # self.count_frame.w['relief']='sunken'

        self.l_baseframe=ttk.Frame(baseframe)
        emptyframe_right=ttk.Frame(baseframe)

        self.l_baseframe.columnconfigure(0, weight=1)
        self.l_baseframe.rowconfigure(0, weight=1)

        self.l_baseframe.columnconfigure(0, weight=1)
        self.l_baseframe.rowconfigure(0, weight=1)

        # emptyframe_right['borderwidth']=2
        # emptyframe_right['relief']='sunken'


        self.l_baseframe.grid(          column=0, row=0, sticky='wnes')
        self.refreshFrame.w.grid(       column=1, row=0, sticky="s")
        self.count_frame.w.grid(        column=2, row=0, sticky="n")
        emptyframe_right.grid(          column=3, row=0, sticky='wnes')
        

        self.console = ttk.Label(self.l_baseframe, anchor='nw', width=30)
        # l.columnconfigure(0, weight=1)
        # l.rowconfigure(0, weight=1)
        f = font.nametofont('TkDefaultFont')
        self.width_in_font_pixels = 30 * f.actual()['size']
        # l['relief']='sunken'
        self.console['wraplength']=self.width_in_font_pixels
        self.console.grid(column=0, row=0, sticky='wnes')
        motd=self.display_messages[0]
        self.message_being_displayed=True
        self.add_text_over_time_to_label(self.console, motd, len(motd))



        # subbaseframe
        subbaseframe = ttk.Frame(root)
        subbaseframe.grid(column=0, row=2)
        self.cpusec_entryframe  = CPUSecFrame(self, subbaseframe)
        self.dursec_entryframe  = DurSecFrame(self, subbaseframe)

        self.cpusec_entryframe.w.grid(  column=1,row=0, sticky="w")
        self.dursec_entryframe.w.grid(  column=2,row=0, sticky="w")

        root.bind('<Escape>', lambda e: root.destroy())




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





    def _update_cmd(self, *args):
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

        if self.cpusec_entryframe.cpusec_entry.instate(['!disabled']) and self.cpusec_entry_var.get():
            ss+= f" AND 'com.pricing.model.linear.coeffs'.cpu_sec <= {Decimal(self.cpusec_entry_var.get())/Decimal('3600.0')}"
         
        if self.dursec_entryframe.durationsec_entry.instate(['!disabled']) and self.durationsec_entry_var.get():
            ss+= f" AND 'com.pricing.model.linear.coeffs'.duration_sec <= {Decimal(self.durationsec_entry_var.get())/Decimal(3600.0)}"

        ss+=" GROUP BY 'node.id'.name"  \
            f" ORDER BY {self.order_by_last}"


        return ss







    def _refresh_cmd(self, *args):
        self.console.grid_remove()
        l = ttk.Label(self.l_baseframe, anchor='nw', width=30)
        l.grid(column=0, row=0, sticky='wnes')
        l['wraplength']=self.width_in_font_pixels
        self.add_text_over_time_to_label(l, self.display_messages[1], len(self.display_messages[1]))
        # self.add_text_over_time_to_label(self.console, self.display_messages[1], len(self.display_messages[1]))
        self.refreshFrame._toggle_refresh_controls()

        self.resultcount_var.set("")
        self.resultdiffcount_var.set("")
        self.tree.delete(*self.tree.get_children())
        self.tree.update_idletasks()

        ss = self._update_or_refresh_sql()

        self.session_id=str(datetime.now().timestamp())
        msg_out = {"id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} }
        self.q_out.put_nowait({"id": self.session_id, "msg": { "subnet-tag": self.subnet_var.get(), "sql": ss} })
        results=None
        msg_in = None

        self.root.after(1, self.handle_incoming_result)







    def handle_incoming_result(self, refresh=True):
        try:
            msg_in = self.q_in.get_nowait()
        except multiprocessing.queues.Empty:
            msg_in = None
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

        if msg_in:
            results = msg_in["msg"]
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


        # tree.tag_configure('Theading', background='green')
        # self.tree.grid(column=0,row=0, columnspan=2, sticky="news")
        self.tree.column('#0', width=0, stretch=NO)
        self.tree.column('offerRowID', width=0, stretch=NO)
        self.tree.column('name', width=0)
        self.tree.column('address', width=0)
        self.tree.column('cpu', width=0)
        self.tree.column('duration', width=0)
        self.tree.column('fixed', width=0)
        self.tree.column('cores', width=0)
        self.tree.column('threads', width=0)

        self.tree.heading('name', text='name', anchor="w" 
                , command=lambda *args: self._update_cmd({"sort_on": "'node.id'.name"})
                )
        self.tree.heading('address', text='address', anchor="w"
                , command=lambda *args: self._update_cmd({"sort_on": "'offers'.address"})
                )
        self.tree.heading('cpu', text='cpu (/sec)', anchor="w"
                , command=lambda *args: self._update_cmd({"sort_on": "'com.pricing.model.linear.coeffs'.cpu_sec"})
                )
        self.tree.heading('duration', text='duration (/sec)', anchor="w"
                , command=lambda *args: self._update_cmd({"sort_on": "'com.pricing.model.linear.coeffs'.duration_sec"})
                )
        self.tree.heading('fixed', text='fixed', anchor="w"
                , command=lambda *args: self._update_cmd({"sort_on": "'com.pricing.model.linear.coeffs'.fixed"})
                )
        self.tree.heading('cores', text='cores', anchor="w"
                , command=lambda *args: self._update_cmd({"sort_on": "'inf.cpu'.cores"})
                )
        self.tree.heading('threads', text='threads', anchor="w"
                , command=lambda *args: self._update_cmd({"sort_on": "'inf.cpu'.threads"})
                )

        # tree.insert('', 'end', values=('namevalue', 'addressvalue', 'cpuvalue', 'durationvalue', 'fixedvalue'))
        root.mainloop()


