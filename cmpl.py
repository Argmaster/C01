from py_compile import compile


if __name__ == "__main__":
    compile("./bin/synclib/config.py", cfile="./synclib/config.pyc")
    compile("./bin/synclib/daemon.py", cfile="./synclib/daemon.pyc")
    compile("./bin/synclib/encryption.py", cfile="./synclib/encryption.pyc")
    compile("./bin/client.py", cfile="./client.pyc")