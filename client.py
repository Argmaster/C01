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


@Daemon(delay=0.5)
def pullFile(var, setup):
    fileData = requests.get(
        f"http://{setup['address']}{':'+setup['port'] if setup['port'] else ''}/getFile"
    ).content
    var.set(var.get() + len(fileData))
    # throws requests.exceptions.ConnectionError !!!
    if setup["encode"]:
        fileData = b"".join(decrypt(fileData, setup["encode_key"]))
    with open(setup["target"], "wb") as file:
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


class UnwantedConnectionError(Exception):
    pass


class ConnectionWindow(tk.Toplevel, Widget):

    entryWidgets: dict = None
    setup: dict = None
    innerFrame: tk.Frame = None
    performPulling = False
    labelWidgets = None
    uploadedDataVar = None
    downloadedDataVar = None
    downloadLabelVar = None
    pollingRateVar = None

    def __init__(self, master: tk.Widget, setup: dict):
        """Connection top level window with polling control

        Args:
            master (tk.Widget): parent (master) widget
            setup (dict): dictionay containing configuration
        """
        super().__init__(master)
        # set configuration variables
        self.pollingRateVar = tk.IntVar(value=500)
        self.uploadedDataVar = tk.IntVar(value=0)
        self.downloadedDataVar = tk.IntVar(value=0)
        self.downloadLabelVar = tk.StringVar()
        # add tracebacks to them
        self.downloadedDataVar.trace("w", self.updateDownloadLabel)
        self.pollingRateVar.trace("w", self.updatePollingRate)
        # clone reference to setup
        self.setup = setup
        # set main widget of this window
        self.innerFrame = wFrame(self)
        self.innerFrame.pack(pady=10, padx=10)
        # window setup behavior
        self.attributes("-topmost", True)
        self.geometry(f"+{self.master.master.winfo_x()}+{self.master.master.winfo_y()}")
        self.title("Connection")
        # disable all entries in parent window
        for _ in map(
            lambda w: w.configure(state="disabled"),
            self.master.entryWidgets.values(),
        ):
            pass
        # add widgets of this window
        self._insertWidgets()
        self._insertBindings()
        # initialize connection
        if not self.__init_connection__():
            self.destroy()
            return None

    def getData(self, url: str):
        """Send get request to server defined
        by setup provided to constructor

        Args:
            url (str): url path to resource

        Raises:
            FatalResponseCode: If status code of request
                                is not equal 200

        Returns:
            bytes: bytes of response content
        """
        response = requests.get(
            f"http://{self.setup['address']}{':'+self.setup['port'] if self.setup['port'] else ''}{url}"
        )
        if response.status_code != 200:
            raise FatalResponseCode(response.status_code)
        response = response.content
        self.downloadedDataVar.set(self.downloadedDataVar.get() + len(response))
        return response

    def __init_connection__(self):
        """Initial test of connection with server
        provided in setup, just asks for some fixed
        header and tests if it can be decoded and
        it there are any connection issues

        Returns:
            bool: True if was succesfull, False otherwise
        """
        try:
            response = self.getData("/connect")
            if self.setup["encode"]:
                response = json.loads(
                    b"".join(decrypt(response, self.setup["encode_key"])).decode(
                        "utf-8"
                    )
                )
                if not response["success"]:
                    raise UnwantedConnectionError()
                self.master.config["allow_edit"] = response["allow_edit"]
            return True
        except (json.JSONDecodeError, UnicodeDecodeError):
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
        except UnwantedConnectionError:
            tkmsb.showerror(
                "Error",
                f"Server is not likely to talk with us :C",
            )
            return False

    def updateDownloadLabel(self, *args, **kwargs):
        val = self.downloadedDataVar.get()
        if val < 1024:
            val = f"Pulled: {val} B"
        elif val < 1048576:
            val = f"Pulled: {val/1024:.2f} KiB"
        elif val < 1073741824:
            val = f"Pulled: {val/1048576:.2f} MiB"
        else:
            val = f"Pulled: {val/1099511627776:.2f} GiB"
        self.downloadLabelVar.set(val)

    def updatePollingRate(self, *args):
        pullFile.delay = self.pollingRateVar.get() / 1000

    def _insertBindings(self):
        self.protocol("WM_DELETE_WINDOW", self.endConnection)

    def _insertWidgets(self):
        self.labelWidgets = {
            "ip_info": self.innerFrame.gridIn(
                tk.Label,
                {
                    "text": f"Server: {self.setup['address']}{':'+self.setup['port'] if self.setup['port'] else ''}",
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
                {"width": 25, "textvariable": self.downloadLabelVar},
                {
                    "row": 2,
                    "column": 1,
                    "sticky": "s",
                },
            ),
            "polling_rate": self.innerFrame.gridIn(
                tk.Label,
                {"width": 25, "text": "Polling Interval (ms)"},
                {
                    "row": 3,
                    "column": 0,
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
                    "text": "Stop Pulling",
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
            "polling_rate": self.innerFrame.gridIn(
                tk.Scale,
                {
                    "orient": tk.HORIZONTAL,
                    "length": 200,
                    "from": 100,
                    "to": 5000,
                    "variable": self.pollingRateVar,
                },
                {"row": 3, "column": 1},
            ),
        }
        self.updateDownloadLabel()

    def startPulling(self, *args):
        """Initializes pullFile daemon, sets performPulling flag to true"""
        self.performPulling = True
        self.entryWidgets["startPulling"]["state"] = "disabled"
        self.entryWidgets["stopPulling"]["state"] = "normal"
        pullFile(self.downloadedDataVar, self.master.config)

    def stopPulling(self, *args):
        """Terminates pullFile daemon, sets performPulling flag to false"""
        self.performPulling = False
        self.entryWidgets["startPulling"]["state"] = "normal"
        self.entryWidgets["stopPulling"]["state"] = "disabled"
        pullFile.kill()

    def endConnection(self, *args):
        """Kills pulling daemon and destroys the connection windows"""
        if self.performPulling:
            if not tkmsb.askyesno("Alert", "Do you want to close connection?"):
                return None
            self.entryWidgets["startPulling"]["state"] = "disabled"
            self.entryWidgets["stopPulling"]["state"] = "disabled"
            self.entryWidgets["endConnection"]["state"] = "disabled"
            self.stopPulling()
        self.destroy()

    def destroy(self):
        """Destroy this window and activate entries in main window"""
        self.master.connectionSubWindow = None
        self.master.hasActiveConnection = False
        # while connection window is created, enties
        # in main window are made disabled, reverse it here
        for _ in map(
            lambda w: w.configure(state="normal"),
            self.master.entryWidgets.values(),
        ):
            pass
        # call parent method to keep the default functionality
        return super().destroy()


class Window(tk.Frame, Widget):

    hasActiveConnection = False
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
        self.master.attributes("-topmost", True)
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
        if not self.hasActiveConnection:
            self.connectionSubWindow = ConnectionWindow(self, setup)
        else:
            tkmsb.showwarning(
                "Connection", "Only one connection can be started at once"
            )


if __name__ == "__main__":
    root = tk.Tk()
    Window(root)
    root.mainloop()
