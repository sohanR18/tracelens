"""Loopback-only, dependency-free HTTP API and dashboard."""
import json, argparse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from engine import investigate, DEMO
ROOT=Path(__file__).parent
class Handler(BaseHTTPRequestHandler):
 def respond(self,status,data,kind="application/json"):
  body=json.dumps(data).encode() if kind=="application/json" else data
  self.send_response(status); self.send_header("Content-Type",kind); self.send_header("Content-Length",str(len(body))); self.send_header("X-Content-Type-Options","nosniff"); self.end_headers(); self.wfile.write(body)
 def do_GET(self):
  if self.path=="/api/demo": return self.respond(200,{"events":DEMO})
  if self.path=="/api/health": return self.respond(200,{"status":"ok"})
  files={"/":"index.html","/app.js":"app.js","/style.css":"style.css"}
  if self.path not in files: return self.respond(404,{"error":"Not found"})
  f=ROOT/"static"/files[self.path]
  self.respond(200,f.read_bytes(),{".html":"text/html; charset=utf-8",".js":"text/javascript",".css":"text/css"}[f.suffix])
 def do_POST(self):
  if self.path!="/api/investigate": return self.respond(404,{"error":"Not found"})
  if self.headers.get("Origin") and self.headers["Origin"]!=f"http://{self.headers.get('Host')}": return self.respond(403,{"error":"Cross-origin requests are disabled"})
  try:
   size=int(self.headers.get("Content-Length",0))
   if size<1 or size>2000000: raise ValueError("Request must be between 1 byte and 2 MB")
   data=json.loads(self.rfile.read(size)); self.respond(200,investigate(data.get("events"),data.get("excluded")))
  except (ValueError,TypeError,AttributeError) as e: self.respond(400,{"error":str(e)})
if __name__=="__main__":
 parser=argparse.ArgumentParser(); parser.add_argument("--port",type=int,default=8080); args=parser.parse_args()
 print(f"TraceLens running at http://127.0.0.1:{args.port}",flush=True)
 ThreadingHTTPServer(("127.0.0.1",args.port),Handler).serve_forever()
