from synclib.encryption import EncryptionKey, encrypt, decrypt
import json


def getFile(env: dict, response: callable, config: dict):
    output = b""
    if config["target"]:
        with open(config["target"], "rb") as file:
            output = file.read()
        if config["encode"]:
            output = b"".join(encrypt(output, config["encode_key"]))
    response("200", [("Content-Type", "text/html")])
    return [output]


def connect(env: dict, response: callable, config: dict):
    response("200", [("Content-Type", "text/html")])
    data = {
        "success": True,
        "allow_edit": config["allow_edit"],
    }
    data = json.dumps(data).encode("utf-8")
    if config["encode"]:
        data = b"".join(encrypt(data, config["encode_key"]))
    return [data]


URLS = {"/getFile": getFile, "/connect": connect}