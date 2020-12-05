import asyncio
import functools
import hashlib
import os
import re
import threading
from altimeter_desktop_tool import __version__
from altimeter_desktop_tool.gui.TextConsole import TextConsole
from cli import get_user_target_pi
from altimeter_desktop_tool.ssh_helpers import MySshClient

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import simpledialog
    from tkinter import filedialog
except:
    import Tkinter as tk
    from Tkinter import ttk


def make_threaded(fn):
    def __inner(*args,**kwargs):
        if threading.current_thread().name == "MainThread":
            threading.Thread(target=fn,args=args,kwargs=kwargs).start()
        else:
            return fn(*args,**kwargs)
    return __inner

@make_threaded
def async_stream_stdout(sshCli, cmd, outputCallback,onDoneCallback=None):
    for line in sshCli.iter_stdout(cmd):
        outputCallback(line)
    if onDoneCallback:
        onDoneCallback()

@make_threaded
def async_check_stdout(sshCli,cmd,*outputCallbacks):
    result = sshCli.check_stdout(cmd)
    for outputCallback in outputCallbacks:
        outputCallback(result)

@make_threaded
def async_identify_rpi(callback):
    pi = get_user_target_pi(yes=True)
    callback(pi)

def class_with_root_call_in_main(fn):
    def __inner(self,*args,**kwargs):
        if threading.current_thread().name == "MainThread":
            fn(self,*args,**kwargs)
        else:
            return self.root.after(1,lambda:fn(self,*args,**kwargs))
    return __inner
    # ip = pi.getpeername()[0]
    # self.textWindow.insert(tk.END, "\nFound: %s" % ip)
    # self.textWindow.see(tk.END)
    #
    # self.findpi.config(state=tk.DISABLED, text="CONNECTED: %s" % ip)
    # self.disconnectpi.config(state=tk.NORMAL)
    # self.logs_submenu.entryconfig("Streaming", state=tk.NORMAL)
    # self.logs_submenu.entryconfig("Downloads", state=tk.NORMAL)
    # for line in sshCli.iter_stdout(cmd):
    #     outputCallback(line)

class Layout:
    def download(self,remote_src,local_dst):
        self.pi.download_file(remote_src,local_dst)
    def set_downloads_files(self,result):
        def do_download(what):
            try:
                what = what.decode('utf8','ignore')
            except:
                print("ERROR:",what)
            filetypes = [[os.path.basename(what)]*2]
            print("DL:",what)

            local_path = filedialog.asksaveasfilename(title = "Save As",filetypes=filetypes,
                                                  initialfile=filetypes[0][0])
            if not local_path:
                return
            self.download(what,local_path)

            simpledialog.messagebox.showinfo(b"Download Success","Downloaded %s"%local_path)
            self.textWindow.insert(tk.END,"\nDownloaded %s\n"%local_path)
        def do_download_all():
            local_path = filedialog.asksaveasfilename(title="Save As", filetypes=[["logfiles.tar"]*2],
                                                      initialfile="logfiles.tar")
            if not local_path:
                return
            self.stream_command_to_shell("tar -cvf ~/logfiles.tar /logfiles/*",True,do_download('~/logfiles.tar'))
            self.download("~/logfiles.tar", local_path)
        # self._root_menu_logs.entryconfig("Downloads",)
        logs_download_menu = tk.Menu(self._root_menu_logs, tearoff=0)
        logs_download_menu.add_command(label="All",command=lambda:do_download_all())
        logs_download_menu.add_command(label="Refresh",command=lambda :async_check_stdout(self.pi,"ls /logfiles",self.set_downloads_files))
        logs_download_menu.add_separator()
        for  result in result.splitlines():
            logs_download_menu.add_command(label=result,command=functools.partial(do_download,b"/logfiles/%s"%result))
        self._root_menu_logs.entryconfig("Downloads", menu=logs_download_menu)

    def setup_menu(self):
        self.menu = tk.Menu(self.root)
        filemenu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=filemenu)
        self._root_menu_logs = logs = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Logs", menu=logs,state=tk.DISABLED)
        workers = tk.Menu(self.menu,tearoff=0)
        workers1 = tk.Menu(workers,tearoff=0)
        workers2 = tk.Menu(workers,tearoff=0)
        verb1 = tk.Menu(workers1,tearoff=0)
        verb2 = tk.Menu(workers2,tearoff=0)
        workers.add_cascade(label="Serial Monitor",menu=workers1)
        workers.add_cascade(label="Gui Application",menu=workers2)
        def systemctl(workername,action):
            print("EXEC:",workername,action)
            self.command_output_to_shell("sudo systemctl %s %s"%(action,workername),True)
        def set_verbosity(pkill_code,verbosity):
            code = {"DEBUG":29,"INFO":10,"WARN":12}[verbosity.upper()]
            self.command_output_to_shell("sudo pkill -%s -f %s" % (code,pkill_code), True)
            # self.pi.sudo_pkill(pkill_code,code)
        for i in ("DEBUG","INFO","WARN"):
            verb1.add_command(label=i,command=functools.partial(set_verbosity,"SerialWorker/main",i))
            verb2.add_command(label=i,command=functools.partial(set_verbosity,"gui/main",i))
        workers1.add_cascade(label="verbosity",menu=verb1)
        workers2.add_cascade(label="verbosity",menu=verb2)
        for i in ("status","restart","start","stop"):
            workers1.add_command(label=i,command=functools.partial(systemctl,"ser-mon",i))
            workers2.add_command(label=i,command=functools.partial(systemctl,"altimeter",i))
        self.menu.add_cascade(label="Workers", menu=workers,state=tk.DISABLED)
        logs_stream_menu = tk.Menu(logs,tearoff=0)
        logs_download_menu = tk.Menu(logs,tearoff=0)
        logs.add_cascade(label="Streaming",menu=logs_stream_menu)
        logs.add_cascade(label="Downloads",menu=logs_download_menu)

        logs_stream_menu.add_command(label="Both",command=lambda:self.stream_log("ser-mon","altimeter"))
        logs_stream_menu.add_command(label="Serial Monitor",command=lambda:self.stream_log("ser-mon"))
        logs_stream_menu.add_command(label="Gui Application",command=lambda:self.stream_log("altimeter"))
        # logs_stream_menu.add_command(label="Stop Streaming",state=tk.DISABLED)
        logs_download_menu.add_command(label="All")
        logs_download_menu.add_command(label="gps_raw.txt")
        logs_download_menu.add_command(label="main_gui.log")
        logs_download_menu.add_command(label="main-serial-worker.log")


        self.logs_stream_menu = logs_stream_menu
        self.logs_download_menu = logs_download_menu
        self.logs_submenu = logs
        self.logs_submenu.entryconfig("Streaming", state=tk.DISABLED)
        self.logs_submenu.entryconfig("Downloads", state=tk.DISABLED)
        # logs_download_menu.config(state=tk.DISABLED)
        # logs_stream_menu.config(state=tk.DISABLED)
        # filemenu.add_command(label="Save", command=donothing)
        # filemenu.add_command(label="Save as...", command=donothing)
        # filemenu.add_command(label="Find PI and Connect", command=lambda:self.search_pi(None))
        filemenu.add_command(label="Close", command=self.root.quit)

        self.root.config(menu=self.menu)
        def get_input(evt):
            ident = hashlib.md5(os.urandom(32))
            if self.pi:
                result = simpledialog.askstring("Exec Remote","Enter Remote Command")
                if not result:
                    return
                # result = result.rstrip(";") + "; # INSTALLJOB %s" % ident
                self.command_output_to_shell(result,show_prompt=True)
                # self.textWindow.insert(tk.END,"\n\npi@%s:~ $ %s\n"%(self.pi.getpeername()[0],result))
                # async_check_stdout(self.pi,result,self.on_line)
            return ident
        def get_input2(evt):
            ident = hashlib.md5(os.urandom(32))
            if self.pi:
                result = simpledialog.askstring("Exec Remote Stream","Enter Remote Command")
                # journalctl -u ser-mon -f -n 1
                if not result:
                    return
                self.stream_command_to_shell(result,True)
                # self.cmd = result.replace(" ","\\ ")
                # # journalctl -u ser-mon -f -n 1
                # # result = "INSTALLJOB=%s;"%ident.hexdigest()+result
                # self.textWindow.insert(tk.END,"\n\npi@%s:~ $ %s [stream]\n"%(self.pi.getpeername()[0],result))
                # async_stream_stdout(self.pi,result,self.on_line)
            return ident
        def kill(*args):
            if self.pi: # and self.cmd:
                assert isinstance(self.pi,MySshClient)
                self.pi.close()
                self.pi.reconnect()
                self.textWindow.insert(tk.END,"*** Client Restarted ***")

                self.logs_stream_menu.entryconfig("Serial Monitor", state=tk.NORMAL)
                self.logs_stream_menu.entryconfig("Gui Application", state=tk.NORMAL)
                self.logs_stream_menu.entryconfig("Both", state=tk.NORMAL)

        self.root.bind("<Control-e>", get_input)
        self.root.bind("<Control-r>", get_input2)
        self.root.bind("<Control-c>", kill)

    def __init__(self,master):
        self.root = master
        self.setup_menu()
        top = tk.Frame(self.root)
        self.pi = None
        self.findpi = tk.Button(top,text="Find Pi",command=self.search_pi)
        self.findpi.pack(side=tk.RIGHT,fill=tk.BOTH,expand=1)
        self.disconnectpi = tk.Button(top,text="Disconnect",state=tk.DISABLED,command=self.disconnect)
        self.disconnectpi.pack(side=tk.RIGHT)
        top2 = tk.Frame(self.root)
        self.run_btn = tk.Button(top2,text="Install Altimeter",state=tk.DISABLED,command=self.do_run)
        self.run_btn.pack(side=tk.LEFT,expand=1,fill=tk.X)
        # self.logs1_btn = tk.Button(top2, text="DOWNLOAD LOGS", state=tk.DISABLED, command=self.do_run)
        # self.logs1_btn.pack(side=tk.LEFT)
        # self.logs2_btn = tk.Button(top2, text="STREAM LOGS", state=tk.DISABLED, command=self.do_run)
        # self.logs2_btn.pack(side=tk.LEFT)
        top.pack(side=tk.TOP,fill=tk.X)
        top2.pack(side=tk.TOP,fill=tk.X)
        # s = "\n".join("initialize-%s"%i for i in range(2))

        self.textWindow = TextConsole(self.root)
        self.textWindow.bind_command(self.on_user_command)
        self.textWindow.pack(side=tk.BOTTOM,expand=1,fill=tk.BOTH)
        self.root.after(100,self.search_pi)

    def do_run(self):
        print("RUN")
        if self.run_btn['text'] == "UPDATE FROM WEB":
            self.stream_command_to_shell('cd python_altimeter_pkg && sudo git pull')
        else:
            simpledialog.messagebox.showinfo("INSTALL ALTIMETER",
            "You might want to go grab a cup of coffee this might take a while...")
            print("LETS INSTALL IT....")
            base_repo = "https://raw.githubusercontent.com/joranbeasley/python_altimeter_pkg/master"
            url = base_repo+"/install_scripts/wget_installer.sh"
            cmd = "curl  %s| sudo sh"%url
            self.stream_command_to_shell(cmd,True)
    def disconnect(self):
        self.pi.close()
        self.pi = None
        self.logs_submenu.entryconfig("Streaming", state=tk.DISABLED)
        self.logs_submenu.entryconfig("Downloads", state=tk.DISABLED)
        self.findpi.config(state=tk.NORMAL, text="Find Pi")
        self.disconnectpi.config(state=tk.DISABLED)

    @class_with_root_call_in_main
    def on_line(self,line):
        print("GOT LINE:",line)
        # def handle_line():
        #     print("thread == "+threading.current_thread().name,"Line:",line)
        self.textWindow.add_text(line)
        self.textWindow.see(tk.END)
    def on_user_command(self,cmd):
        print("GOT USER CMD:",repr(cmd))
        if cmd.startswith("cd") and ";" not in cmd:
            self.textWindow.add_text("[\033[1;33mERROR:\033[0m]] All comands are executed from the $HOME directory")
        else:
            async_stream_stdout(self.pi,cmd,self.on_line,self.on_ready)
    @class_with_root_call_in_main
    def on_ready(self,*args):
        self.textWindow.insert(tk.END,"\n")
        self.textWindow.show_user_prompt()
    @class_with_root_call_in_main
    def on_altimeter_install_state(self,state):
        if state.lower().strip() not in  {b'true','true'}:
            self.textWindow.insert(tk.END, "No Existing Installation Found\n"%state)
            self.run_btn.config(state=tk.NORMAL)
        else:
            self.textWindow.insert(tk.END, "Existing Installation Found\n")
            self.run_btn.config(state=tk.NORMAL,text="UPDATE FROM WEB")
            self.logs_submenu.entryconfig("Streaming", state=tk.NORMAL)
            async_check_stdout(self.pi,"ls /logfiles",self.set_downloads_files)
            async_stream_stdout(self.pi,"systemctl status ser-mon altimeter -n 0",self.on_line,self.on_ready)
            self.logs_submenu.entryconfig("Downloads", state=tk.NORMAL)
            self.menu.entryconfig("Logs",state=tk.NORMAL)
            self.menu.entryconfig("Workers",state=tk.NORMAL)
    def show_prompt(self,cmd):
        self.textWindow.insert(tk.END, "\n\npi@%s:~ $ %s\n" % (self.pi.getpeername()[0], cmd))
    def stream_command_to_shell(self,cmd,show_prompt=False,onDone=None):
        if show_prompt:
            self.show_prompt(cmd)
        async_stream_stdout(self.pi,cmd,self.on_line,onDone)
    def command_output_to_shell(self,cmd,show_prompt=False,onDone=None):
        if show_prompt:
            self.show_prompt(cmd)
        cb = self.on_line
        if onDone:
            cb = [self.on_line,onDone]
        async_check_stdout(self.pi, cmd, self.on_line)
    # @class_with_root_call_in_main
    # def on_job_state(self,txt):
    #     self.textWindow.insert(tk.END,txt.decode('ascii','ignore'))
    @class_with_root_call_in_main
    def on_pi_found(self,conn):
        # def updateui():
        print("UPDATE UI:",threading.current_thread())
        if not conn:
            self.findpi.config(state=tk.DISABLED, text="Searching ...")
            self.textWindow.insert(tk.END, "\033[1;33m.\033[0m]")
            self.textWindow.see(tk.END)
            return
        self.pi = conn
        ip = conn.getpeername()[0]
        self.findpi.config(state=tk.DISABLED, text="CONNECTED: %s" % ip)
        self.disconnectpi.config(state=tk.NORMAL)
        self.textWindow.insert(tk.END, "\nFound: %s\n"%ip)
        self.textWindow.see(tk.END)
        pycmd = "import os;print('python_altimeter_pkg' in os.listdir('/home/pi'));"
        cmd = "python -c \"%s\""%pycmd
        async_check_stdout(self.pi,cmd,self.on_altimeter_install_state)
        # pycmd = "import os;print('python_altimeter_pkg2' in os.listdir('/home/pi'));"
        # cmd = "python -c \"%s\"" % pycmd
        # async_check_stdout(self.pi,cmd, self.on_altimeter_install_state)
        # pycmd = "import os;print('python_altimeter_pkg' in os.listdir('/home/pi2'));"
        # cmd = "python -c \"%s\"" % pycmd
        # async_check_stdout(self.pi, cmd, self.on_altimeter_install_state)

    def search_pi(self,*evt):
        self.findpi.config(state=tk.DISABLED, text="Searching ...")
        self.textWindow.insert(tk.INSERT, "SEARCHING FOR RASPBERRY PY")
        self.textWindow.see(tk.END)
        async_identify_rpi(self.on_pi_found)

    def stream_log(self,*units):
        simpledialog.messagebox.showinfo("Streaming","Use Ctrl+c to cancel")
        s = ["-u %s"%u for u in units]
        self.logs_stream_menu.entryconfig("Serial Monitor",state=tk.DISABLED)
        self.logs_stream_menu.entryconfig("Gui Application",state=tk.DISABLED)
        self.logs_stream_menu.entryconfig("Both", state=tk.DISABLED)
        cmd = "journalctl %s -f"%" ".join(s)
        async_stream_stdout(self.pi, cmd, self.on_line)
class App:
    def __init__(self):
        self.root = tk.Tk(className='Setup Altimeter v%s'%(__version__))
        self.layout = Layout(self.root)
        # w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        # self.root.geometry("%dx%d+0+0" % (w, h))
        self.root.wm_state('zoomed')
        # self.root.config(title="Setup Altimeter")
        self.root.mainloop()

if __name__ == "__main__":
    App()

