import json
import os
from typing import Any


class CFG:
    """Configuration dictionary wrapper class"""

    DEFAULT_CONFIG = {}

    def __init__(self, path: str = "./.cfg") -> None:
        """Set path and default config
        call load method to load config
        form local file

        Args:
            path (str, optional): path to config file. Defaults to "./.cfg".
        """
        self._config = self.DEFAULT_CONFIG
        self.path = path
        self.load()

    def load(self) -> None:
        """Try to load config form file,
        if it is not posibble (ie. exception occurs)
        call save() method which will create
        necessary files
        """
        try:
            # context manager -> load json config
            with open(self.path) as file:
                self._config = json.load(file)
        except Exception:
            # in case of exception, default config is used
            self._config = self.DEFAULT_CONFIG
            # and default config is being saved to file
            self.save()

    def __getitem__(self, key: str) -> Any:
        """Get item magic method, provides
        instance[key] sequence indexing
        syntax sugar

        Args:
            key (str): config dictionary key

        Returns:
            ususally str: config value
        """
        return self._config.get(key, self.DEFAULT_CONFIG[key])

    def __setitem__(self, key: str, value: Any) -> None:
        """Set config value and save whole config to file

        Args:
            key (str): key to be used to select value
            value (many): value to be set for given key in config
        """
        self._config[key] = value

    def save(self) -> None:
        """Save current config to file,
        Can be called while config is missing
        """
        with open(self.path, "w") as file:
            json.dump(self._config, file, indent="    ", sort_keys=True)


class ServerCFG(CFG):
    """Changes default config from CFG class"""

    DEFAULT_CONFIG = {
        "target": "",
        "allow_edit": False,
        "encode": True,
        "encode_key": "",
    }


class ClientCFG(CFG):
    """Changes default config from CFG class"""

    DEFAULT_CONFIG = {
        "target": "./databuffer.txt",
        "encode_key": "",
        "encode": True,
        "allow_edit": False,
        "address": "",
        "port": "8080",
    }