import http.server, sys, os
D = sys.argv[1]
class H(http.server.BaseHTTPRequestHandler):
    def _c(self):
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Headers", "*"); self.send_header("Access-Control-Allow-Private-Network", "true")
    def do_OPTIONS(self): self.send_response(204); self._c(); self.end_headers()
    def do_POST(self):
        n = int(self.headers["Content-Length"]); data = self.rfile.read(n)
        nome = os.path.basename(self.path.strip("/")) or "post.bin"
        open(os.path.join(D, nome), "wb").write(data)
        self.send_response(200); self._c(); self.end_headers(); self.wfile.write(b"ok")
http.server.HTTPServer(("127.0.0.1", 8765), H).serve_forever()
