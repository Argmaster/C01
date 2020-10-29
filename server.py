import waitress
import get
import put
import synclib.config as config

"""
REMOTE_ADDR 192.168.1.181
REMOTE_HOST 192.168.1.181
REMOTE_PORT 53842
REQUEST_METHOD GET
SERVER_PORT 8080
SERVER_NAME spetz-pc
SERVER_SOFTWARE waitress
SERVER_PROTOCOL HTTP/1.1
SCRIPT_NAME
PATH_INFO /
QUERY_STRING
wsgi.url_scheme http
wsgi.version (1, 0)
wsgi.errors <_io.TextIOWrapper name='<stderr>' mode='w' encoding='UTF-8'>
wsgi.multithread True
wsgi.multiprocess False
wsgi.run_once False
wsgi.input <_io.BytesIO object at 0x00007fd03b0fe368>
wsgi.file_wrapper <class 'waitress.buffers.ReadOnlyFileBasedBuffer'>
wsgi.input_terminated True
HTTP_HOST 192.168.1.181:8080
HTTP_USER_AGENT Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0
HTTP_ACCEPT text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
HTTP_ACCEPT_LANGUAGE en-US,en;q=0.5
HTTP_ACCEPT_ENCODING gzip, deflate
HTTP_CONNECTION keep-alive
HTTP_UPGRADE_INSECURE_REQUESTS 1
"""


def main(env: dict, response: callable):
    cfg = config.ServerCFG("./server.cfg")
    try:
        if env["REQUEST_METHOD"] == "GET":
            return get.handleRequest(env, response, cfg)
        elif env["REQUEST_METHOD"] == "PUT":
            return put.handleRequest(env, response, cfg)
        else:
            response("404", [("Content-Type", "text/html")])
            return [b""]
    except ValueError:
        response("500", [("Content-Type", "application/octet-stream")])
        return [b""]


if __name__ == "__main__":
    config.ServerCFG("./server.cfg")
    waitress.serve(main, host="0.0.0.0", port="8080")
