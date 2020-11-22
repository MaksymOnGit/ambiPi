from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os, sys
from typing import Dict, Callable, Tuple
import json
from threading import Thread
from PyAccessPoint import pyaccesspoint

def CustomHTTPRequestHandlerClass(api: Dict[str, Tuple[Callable, tuple]]):
    class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.api: Dict[str, Tuple[Callable, tuple]] = api
            super().__init__(*args, directory=os.path.join(sys.path[0], "www/"), **kwargs)
        def _set_response(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

        def do_GET(self):
            if self.path.startswith("/api"):
                if self.api[self.path] != None:
                    response = None
                    if type(self.api[self.path]) is tuple:
                        response = self.api[self.path][0](*self.api[self.path][1])
                    else:
                        response =self.api[self.path]()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                super(CustomHTTPRequestHandler, self).do_GET()
    return CustomHTTPRequestHandler

class AmbiPiWeb:
    def __init__(self, port):
        self.api = dict()
        handler = CustomHTTPRequestHandlerClass(self.api)
        self.srv: TCPServer = TCPServer(("", port), handler)
        self.ap = pyaccesspoint.AccessPoint(ssid = "ambiPi", password = "24681357")

    def addApi(self, api: str, fnc):
        self.api[api] = fnc

    def startServer(self):
        Thread(daemon=True, target=self.srv.serve_forever).start()
        self.ap.start()

    def stopServer(self):
        self.ap.stop()
        self.srv.shutdown()

    def __del__(self):
        self.srv.shutdown()
        self.srv.server_close()