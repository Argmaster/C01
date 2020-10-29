from encryption import EncryptionKey, encrypt, decrypt


def getFile(env: dict, response: callable, config: dict):
    output = b""
    if config["target"]:
        with open(config["target"], "rb") as file:
            output = file.read()
        if config["encode"]:
            output = b"".join(encrypt(output, config["encode_key"]))
    response("200", [("Content-Type", "text/html")])
    return [output]


def handleRequest(env: dict, response: callable, config: dict):
    if env["PATH_INFO"] == "/getFile":
        return getFile(env, response, config)
    else:
        response("404", [("Content-Type", "application/octet-stream")])
        return [b""]
