import tkinter as tk

class Console(tk.Text):
    def __init__(
            self,
            parent,
            disable_var=None,
            debug_var=None, # not used yet
            **kwargs
            ):
        super().__init__(parent, **kwargs)
        self.configure(state=tk.DISABLED)
        # https://stackoverflow.com/questions/54792599/how-can-i-make-a-tkinter-text-widget-unselectable 
        self.bindtags([str(self), str(parent), "all"])
        # self.bind('<FocusIn>', self._debug_event)

        self.configure(wrap="word")

        if disable_var != None:
            self.disable_var = disable_var
            self.disable_var.trace_add('write', self._check_disable)


    def _write(self, txt, length, current=0, time=25, newmsg=True):
        self["state"] = tk.NORMAL
        self.insert("end", txt[current])
        current += 1
        add_time = 0 # no delay unless the following
        if current != length:
            if txt[current - 1] == ".":
                add_time = time * 15
            elif txt[current - 1] == ",":
                add_time = time * 10
            # self["state"] = tk.DISABLED
            self.after(time + add_time, lambda: self._write( txt, length, current, time, newmsg))
            # self["state"] = "disabled"

    def write(self, msg):
        self["state"] = tk.NORMAL
        self.delete("1.0", "end")
        self._write(msg, len(msg))

    def _check_disable(self, *_):
        # write traced to self._check_disable
        if not hasattr(self, 'disable_var'):
            return

        if self.disable_var.get():
            self.variable.widget.configure(state=tk.DISABLED)
            # self.error.set('')
        else:
            self.variable.widget.configure(state=tk.NORMAL)
