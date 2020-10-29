from encryption import EncryptionKey, encrypt, decrypt


def handleRequest(env: dict, response: callable, config: dict):
    response('404', [('Content-Type','text/html')])
    return [b""]
