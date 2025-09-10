from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

def start_frontend():
    handler_class = partial(SimpleHTTPRequestHandler, directory='frontend/dist')
    ThreadingHTTPServer(('0.0.0.0', 8080), handler_class).serve_forever()