import requests
import json
import time
import tkinter as tk
import tkinter.filedialog as tkfdl
import tkinter.messagebox as tkmsb
import tkinter.ttk as ttk
from synclib.encryption import EncryptionKey, decrypt
import synclib.config as config
from synclib.daemon import Daemon


@Daemon(delay=0.5, process=True)
def pullFile(cfg):
    fileData = requests.get(f"http://{cfg['address']}:{cfg['port']}/getFile").content
    # throws requests.exceptions.ConnectionError !!!
    if cfg["encode"]:
        fileData = b"".join(decrypt(fileData, cfg["encode_key"]))
    with open(cfg["target"], "wb") as file:
        file.write(fileData)


class Widget:
    def packIn(self, widget, widget_cfg={}, pack_cfg={}):
        widget = widget(self, **widget_cfg)
        widget.pack(**pack_cfg)
        return widget

    def placeIn(self, widget, widget_cfg={}, pack_cfg={}):
        widget = widget(self, **widget_cfg)
        widget.place(**pack_cfg)
        return widget

    def gridIn(self, widget, widget_cfg={}, pack_cfg={}):
        widget = widget(self, **widget_cfg)
        widget.grid(**pack_cfg)
        return widget


class wFrame(tk.Frame, Widget):
    pass


class FatalResponseCode(Exception):
    def __init__(self, code):
        self.code = code


class ConnectionWindow(tk.Toplevel, Widget):

    entryWidgets: dict = None
    setup: dict = None
    innerFrame: tk.Frame = None

    def __init__(self, master: tk.Widget, setup: dict):
        super().__init__(master)
        self.setup = setup
        self.innerFrame = wFrame(self)
        self.innerFrame.pack(pady=10, padx=10)
        self.attributes("-topmost", True)
        self.geometry(f"+{self.master.master.winfo_x()}+{self.master.master.winfo_y()}")
        self.title("Connection")
        tuple(
            map(
                lambda w: w.configure(state="disabled"),
                self.master.entryWidgets.values(),
            )
        )
        if not self.__init_connection__():
            self.destroy()
            return None
        self._insertWidgets()

    def __init_connection__(self):
        try:
            response = requests.get(
                f"http://{self.setup['address']}:{self.setup['port']}/pullConfig"
            )
            if response.status_code != 200:
                raise FatalResponseCode(response.status_code)
            else:
                data = response.content
                return True
        except json.JSONDecodeError:
            tkmsb.showerror(
                "Error",
                "Parsing server response failed, porobably invalid decryption key was provided.",
            )
            return False
        except requests.ConnectionError:
            tkmsb.showerror(
                "Error",
                "Can`t connect to server with given adress, connection denied.",
            )
            return False
        except FatalResponseCode as e:
            tkmsb.showerror(
                "Error",
                f"Server responded with not positive response code: {e.code}",
            )
            return False

    def _insertWidgets(self):
        self.labelWidgets = {
            "ip_info": self.innerFrame.gridIn(
                tk.Label,
                {
                    "text": f"Server: {self.setup['address']}:{self.setup['port']}",
                    "width": 25,
                },
                {
                    "row": 0,
                    "column": 1,
                    "sticky": "s",
                },
            ),
            "status_info": self.innerFrame.gridIn(
                tk.Label,
                {"text": f"Status: OK", "width": 25},
                {
                    "row": 1,
                    "column": 1,
                    "sticky": "s",
                },
            ),
            "data_info": self.innerFrame.gridIn(
                tk.Label,
                {"text": f"Pulled: 0 KiB", "width": 25},
                {
                    "row": 2,
                    "column": 1,
                    "sticky": "s",
                },
            ),
        }
        self.entryWidgets = {
            "startPulling": self.innerFrame.gridIn(
                tk.Button,
                {"text": "Start Pulling", "command": self.startPulling, "width": 15},
                {"row": 0, "column": 0},
            ),
            "stopPulling": self.innerFrame.gridIn(
                tk.Button,
                {
                    "text": "Start Pulling",
                    "command": self.stopPulling,
                    "width": 15,
                    "state": "disabled",
                },
                {"row": 1, "column": 0},
            ),
            "endConnection": self.innerFrame.gridIn(
                tk.Button,
                {"text": "End Connection", "command": self.endConnection, "width": 15},
                {"row": 2, "column": 0},
            ),
        }

    def startPulling(self, *args):
        self.entryWidgets["startPulling"]["state"] = "disabled"
        self.entryWidgets["stopPulling"]["state"] = "normal"
        pass

    def stopPulling(self, *args):
        self.entryWidgets["startPulling"]["state"] = "normal"
        self.entryWidgets["stopPulling"]["state"] = "disabled"
        pass

    def endConnection(self, *args):
        self.entryWidgets["startPulling"]["state"] = "disabled"
        self.entryWidgets["stopPulling"]["state"] = "disabled"
        self.entryWidgets["endConnection"]["state"] = "disabled"
        self.stopPulling()
        self.destroy()

    def destroy(self):
        self.master.connectionSubWindow = None
        tuple(
            map(
                lambda w: w.configure(state="normal"),
                self.master.entryWidgets.values(),
            )
        )
        return super().destroy()


class Window(tk.Frame, Widget):

    connectionSubWindow = None
    entryWidgets = None
    labelWidgets = None
    notSaved = False

    def __init__(self, master: tk.Tk):
        super().__init__(master)
        # configure styles
        ttk.Style().configure("pad.TEntry", padding=7)
        ttk.Style().configure("pad.TCheckbutton", padding=7, width=40, height=40)
        # set title
        self.master.title("Code exchange client")
        # pack self into the master widget
        self.pack(pady=10, padx=10)
        # load configuration of app
        self.config = config.ClientCFG("./client.cfg")
        # list of entry value varaibles
        self.tkVariables = [
            tk.StringVar(value=self.config["target"]),
            tk.StringVar(value=self.config["encode_key"]),
            tk.BooleanVar(value=self.config["encode"]),
            tk.StringVar(value=self.config["address"]),
            tk.StringVar(value=self.config["port"]),
        ]
        # add traceback for each value
        for index, variable in enumerate(self.tkVariables):
            variable.trace("w", lambda *args: self.onEntryChange(index, *args))
        # add all widgets to gui frame
        self._insertWidgets()
        self._insertBindings()

    def _insertWidgets(self) -> None:
        self.ON_IMAGE = tk.PhotoImage(width=32, height=16)
        self.OFF_IMAGE = tk.PhotoImage(width=32, height=16)
        self.ON_IMAGE.put(("#25cc62",), to=(0, 0, 15, 15))
        self.OFF_IMAGE.put(("#ed1c43",), to=(16, 0, 31, 15))
        self.labelWidgets = {
            "target": self.gridIn(
                tk.Label,
                {"text": "Local File path"},
                {
                    "row": 0,
                    "column": 0,
                    "sticky": "w",
                },
            ),
            "encode_key": self.gridIn(
                tk.Label,
                {"text": "Decryption Key "},
                {
                    "row": 1,
                    "column": 0,
                    "sticky": "w",
                },
            ),
            "encode": self.gridIn(
                tk.Label,
                {"text": "Perform Decryption"},
                {
                    "row": 2,
                    "column": 0,
                    "sticky": "w",
                },
            ),
            "address": self.gridIn(
                tk.Label,
                {"text": "Server address"},
                {
                    "row": 3,
                    "column": 0,
                    "sticky": "w",
                },
            ),
            "port": self.gridIn(
                tk.Label,
                {"text": "Server port"},
                {
                    "row": 4,
                    "column": 0,
                    "sticky": "w",
                },
            ),
        }
        self.entryWidgets = {
            "target": self.gridIn(
                ttk.Entry,
                {
                    "textvariable": self.tkVariables[0],
                    "style": "pad.TEntry",
                    "width": 30,
                },
                {
                    "row": 0,
                    "column": 1,
                    "sticky": "w",
                },
            ),
            "target_find": self.gridIn(
                tk.Button,
                {"text": "Find", "command": self.findTarget, "width": 3},
                {"row": 0, "column": 2},
            ),
            "encode_key": self.gridIn(
                ttk.Entry,
                {
                    "textvariable": self.tkVariables[1],
                    "style": "pad.TEntry",
                    "width": 36,
                },
                {"row": 1, "column": 1, "sticky": "w", "columnspan": 2},
            ),
            "encode": self.gridIn(
                tk.Checkbutton,
                {
                    "variable": self.tkVariables[2],
                    "image": self.OFF_IMAGE,
                    "selectimage": self.ON_IMAGE,
                    "indicatoron": False,
                },
                {"row": 2, "column": 1, "sticky": "w", "padx": 12, "pady": 6},
            ),
            "address": self.gridIn(
                ttk.Entry,
                {
                    "textvariable": self.tkVariables[3],
                    "style": "pad.TEntry",
                    "width": 36,
                },
                {"row": 3, "column": 1, "sticky": "w", "columnspan": 2},
            ),
            "port": self.gridIn(
                ttk.Entry,
                {
                    "textvariable": self.tkVariables[4],
                    "style": "pad.TEntry",
                    "width": 36,
                },
                {"row": 4, "column": 1, "sticky": "w", "columnspan": 2},
            ),
            "connectionButton": self.gridIn(
                tk.Button,
                {"text": "Connect", "command": self.makeConnection, "width": 10},
                {"row": 5, "column": 1, "pady": 5},
            ),
            "saveButton": self.gridIn(
                tk.Button,
                {"text": "Save", "command": self.save, "width": 10},
                {"row": 5, "column": 0, "pady": 5, "stick": "nesw"},
            ),
        }

    def _insertBindings(self):
        # bind window closing events
        self.master.protocol("WM_DELETE_WINDOW", self.exitWindow)
        self.master.bind("<Escape>", self.exitWindow)
        # bind ctrl + s as save config
        self.master.bind("<Control-s>", self.save)
        # bind ctrl + c as create connection
        self.master.bind("<Control-c>", self.makeConnection)

    def exitWindow(self, *args):
        # called while ESC or x window button is pressed
        if (
            self.notSaved
            and tkmsb.askyesno("Alert", "Do you want to leave without saving?")
        ) or not self.notSaved:
            self.master.destroy()
            exit()

    def onEntryChange(self, index, *args):
        # Called while any of config inputs gets changed
        self.notSaved = True
        content = self.tkVariables[index].get().strip()
        output = ""
        for char in content:
            if 32 < ord(char) < 127:
                output += char
        self.tkVariables[index].set(output)
        self.entryWidgets["saveButton"]["background"] = "#3ea1ed"

    def save(self, *args):
        self.config["target"] = self.tkVariables[0].get()
        self.config["encode_key"] = self.tkVariables[1].get()
        self.config["encode"] = self.tkVariables[2].get()
        self.config["address"] = self.tkVariables[3].get()
        self.config["port"] = self.tkVariables[4].get()
        self.config.save()
        self.notSaved = False
        self.entryWidgets["saveButton"]["background"] = "#DDDDDD"

    def findTarget(self, *args):
        path = tkfdl.asksaveasfilename(
            confirmoverwrite=False,
            initialfile="databuffer.py",
            title="Select local buffer file",
        )
        if path:
            self.tkVariables[0].set(path)

    def makeConnection(self, *args):
        # open connection window
        setup = {}
        setup["target"] = self.tkVariables[0].get()
        setup["encode_key"] = self.tkVariables[1].get()
        setup["encode"] = self.tkVariables[2].get()
        setup["address"] = self.tkVariables[3].get()
        setup["port"] = self.tkVariables[4].get()
        if self.connectionSubWindow is None:
            self.connectionSubWindow = ConnectionWindow(self, setup)
        else:
            tkmsb.showwarning(
                "Connection", "Only one connection can be started at once"
            )


if __name__ == "__main__":
    root = tk.Tk()
    Window(root)
    root.mainloop()
