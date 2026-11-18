"""Rebuild then serve the generated site on loopback; no third-party packages."""
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import argparse
from build import build, OUT

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port', type=int, default=8767)
args = parser.parse_args()
build()
handler = partial(SimpleHTTPRequestHandler, directory=str(OUT))
with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
    print(f'Local preview: http://127.0.0.1:{args.port}', flush=True)
    print('Re-run after editing. Press Ctrl+C to stop.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
