#%%
import requests
from synclib.encryption import EncryptionKey, decrypt
import synclib.config as config
import time
from synclib.daemon import Daemon
import tkinter as tk
import tkinter.filedialog as tkfdl
import tkinter.messagebox as tkmgb


@Daemon(delay=0.5, process=True)
def pullFile(cfg):
    fileData = requests.get(f"http://{cfg['address']}:{cfg['port']}/getFile").content
    # throws requests.exceptions.ConnectionError !!!
    if cfg["encode"]:
        fileData = b"".join(decrypt(fileData, cfg["encode_key"]))
    with open(cfg["target"], "wb") as file:
        file.write(fileData)


class Window(tk.Tk):
    def __init__(self):
        super().__init__(self)
        #self.config = config.ClientCFG("./client.cfg")


#%%


