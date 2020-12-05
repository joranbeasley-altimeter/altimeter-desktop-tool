import re
import tkinter as tk
from tkinter import scrolledtext
bgcolors = {
    r"\033[40m":"black",
    r"\033[41m":"red",
    r"\033[42m":"green",
    r"\033[43m":"yellow",
    r"\033[44m":"blue",
    r"\033[45m":"magenta",
    r"\033[46m":"cyan",
    r"\033[47m":"lightgrey",
    r"\033[100m":"dark grey",
    r"\033[101m":"light red",
    r"\033[102m":"light green",
    r"\033[103m":"light yellow",
    r"\033[104m":"light blue",
    r"\033[105m":"light magenta",
    r"\033[106m":"light cyan",
    r"\033[107m":"light grey",
    "\033[40m":"black",
    "\033[41m":"red",
    "\033[42m":"green",
    "\033[43m":"yellow",
    "\033[44m":"blue",
    "\033[45m":"magenta",
    "\033[46m":"cyan",
    "\033[47m":"light grey",
    "\033[100m":"dark grey",
    "\033[101m":"light red",
    "\033[102m":"light green",
    "\033[103m":"light yellow",
    "\033[104m":"light blue",
    "\033[105m":"light magenta",
    "\033[106m":"light cyan"
}
fgcolors = {
    r"\033[1;30m":"black",
    r"\033[1;31m":"red",
    r"\033[1;32m":"green",
    r"\033[1;33m":"yellow",
    r"\033[1;34m":"blue",
    r"\033[1;35m":"magenta",
    r"\033[1;36m":"cyan",
    r"\033[1;37m":"light gray",
    r"\033[1;90m":"dark gray",
    r"\033[1;91m":"lightred",
    r"\033[1;92m":"light green",
    r"\033[1;93m":"light yellow",
    r"\033[1;94m":"light blue",
    r"\033[1;95m":"light magenta",
    r"\033[1;96m":"light cyan",
    r"\033[1;97m":"white",
    "\033[1;30m":"black",
    "\033[1;31m":"red",
    "\033[1;32m":"green",
    "\033[1;33m":"yellow",
    "\033[1;34m":"blue",
    "\033[1;35m":"magenta",
    "\033[1;36m":"cyan",
    "\033[1;37m":"lightgray",
    "\033[1;90m":"darkgray",
    "\033[1;91m":"light red",
    "\033[1;92m":"light green",
    "\033[1;93m":"light yellow",
    "\033[1;94m":"light blue",
    "\033[1;95m":"light magenta",
    "\033[1;96m":"light cyan",
    "\033[1;97m":"white",
}
class TextColor:
    _tags = {}
    @staticmethod
    def get_style_tag(textInst,fg=None,bg=None):
        """

        :param textInst:
        :param fg: CONSOLE COLOR CODE \033[1;##m
        :param bg: CONSOLE COLOR CODE \033[##m
        :return:
        """
        tag = "%s~%s" % (fg, bg)
        if tag not in TextColor._tags:
            textInst.tag_config(tag,foreground=fgcolors.get(fg),background=bgcolors.get(bg))
            TextColor._tags[tag] = True
        return tag

class CursorChangeCustomText(scrolledtext.ScrolledText):
    def __init__(self, *args, **kwargs):
        scrolledtext.ScrolledText.__init__(self, *args, **kwargs)

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, *args):
        cmd = (self._orig,) + args
        result = self.tk.call(cmd)

        # generate an event if something was added or deleted,
        # or the cursor position changed
        if (args[0] in ("insert", "delete") or
            args[0:3] == ("mark", "set", "insert")):
            self.event_generate("<<CursorChange>>", when="tail")
        return result

class TextConsole(tk.Text):
    def bind_command(self,callback):
        self.callback = callback
    def on_key_down(self,evt):
        if not self.editing:
            return "break"
        if evt.keysym in {"Up","BackSpace","Left","Home","Down","Return"}:
            "Do not allow user to go past 'start'"
            if evt.keysym == "Return":
                cmd = self.get(self.editing,tk.END).rstrip("\n")
                self.editing = False
                self.insert(tk.END, "\n")
                self._hi = 0
                print(repr(cmd))
                self.history.append(cmd)
                self.callback(cmd)

                return "break"
            if evt.keysym == "Up":
                if len(self.history) > self._hi:
                    self._hi += 1
                    self.delete(self.editing, self.get_mark())
                    self.insert(tk.END, self.history[-self._hi])
                    self.mark_set(tk.INSERT, self.get_mark())
                return "break"
            if evt.keysym == "Home":
                return "break"
            if evt.keysym == "Down":
                if self._hi > 1:
                    self._hi -= 1
                    self.delete(self.editing,self.get_mark())
                    self.insert(tk.END,self.history[-self._hi])
                    self.mark_set(tk.INSERT,self.get_mark())
                return "break"
            if evt.keysym in {"BackSpace","Left"}:
                pos = list(map(int,self.index(tk.INSERT).split(".")))
                print(pos)
                minpos = list(map(int,self.editing.split(".")))
                if minpos[1] > pos[1] - 1:
                    self.mark_set(tk.INSERT,self.editing)
                    return "break"



        # print("KEY DOWN:",repr(evt.keysym))

    def __init__(self,master):
        self.history = []
        self.callback = lambda c:print("CMD EXEC:",c)
        self._hi = 0
        self.root = master
        self.bg_color = "black"
        self.fg_color = "white"
        self.editing = False
        tk.Text.__init__(self,master,bg=self.bg_color,fg=self.fg_color,
                         insertbackground=self.fg_color, insertwidth=2)#,font="TkFixedFont"
        self.bind("<Key>",self.on_key_down)
        # self.bind("<<CursorChange>>",self.on_cursor_change)
        # self.bind("<Key>",self.on_key_down)
        # self.bind("<KeyRelease>",self.on_key_up)
        # self.mark_set()
        # self.insert(tk.END,"*** SHELL INITIALIZED ***\n-------------------------")
        self.bind("<ButtonRelease-1>",lambda *a:self.enable_editing())
    def get_mark(self):
        return self.index("end-1c")
    def _add_text(self,txt,fg=None,bg=None):
        tag = TextColor.get_style_tag(self,fg,bg)
        mark = self.get_mark()
        self.insert(tk.END,txt)
        self.tag_add(tag,mark,self.get_mark())
    def _tokenize(self,s):
        return re.split(r"(?P<fg>\033\[[\d;]+m]?(?:\033\[[\d;]+m)?)",s)
    def _parse_tokens(self,str):
        bg,fg = self.bg_color,self.fg_color
        for token in self._tokenize(str):
            if token == "\033[0m]":
                bg, fg = self.bg_color, self.fg_color
            elif token.startswith("\033["):
                if "m\033[" in token:
                    fg,bg = token.split("m\033[")
                    fg = fg+"m"
                    bg = "\033["+bg
                elif ";" in token:
                    fg = token
                else:
                    bg = token
            else:
                yield {'fg':fg,'bg':bg,'txt':token}
    def show_user_prompt(self):
        if not self.editing:
            self.add_text("\033[1;32mpi@192.168.1.139\033[0m]:~ $ ")
            self.see(tk.END)
            self.enable_editing()
    def enable_editing(self):
        # print(event)
        if not self.editing:
            self.editing = self.get_mark()
        self.mark_set(tk.INSERT, self.get_mark())
    def add_text(self,txt):
        for token in self._parse_tokens(txt):
            self._add_text(**token)

if __name__ == "__main__":
    root = tk.Tk()
    c = TextConsole(root)
    c.add_text("*** \033[1;33mSystem\033[0m] [\033[1;32mInitialized\033[0m]] ***\n")
    c.add_text("\n\n")
    def on_cmd(cmd):
        c.add_text("RESULT = 6\n")
        c.show_user_prompt()
    c.bind_command(on_cmd)
    c.show_user_prompt()
    c.pack()
    root.mainloop()
