"""Local web demo for Campaign Content QA."""
import json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from campaign_qa import review
ROOT = Path(__file__).parent
class Handler(BaseHTTPRequestHandler):
    def send_data(self, status, data, content_type):
        self.send_response(status); self.send_header("Content-Type", content_type); self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'"); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        routes={"/":("web/index.html","text/html; charset=utf-8"),"/styles.css":("web/styles.css","text/css"),"/app.js":("web/app.js","application/javascript"),"/demo/campaign.json":("demo/campaign.json","application/json"),"/demo/policy.json":("demo/policy.json","application/json")}
        if self.path not in routes: return self.send_data(404,b'{"error":"not found"}',"application/json")
        path,kind=routes[self.path]; self.send_data(200,(ROOT/path).read_bytes(),kind)
    def do_POST(self):
        try:
            size=int(self.headers.get("Content-Length","0")); payload=json.loads(self.rfile.read(size)); result=review(payload["campaign"],payload["policy"]); self.send_data(200,json.dumps(result).encode(),"application/json")
        except (ValueError,KeyError,json.JSONDecodeError) as exc: self.send_data(400,json.dumps({"error":str(exc)}).encode(),"application/json")
if __name__=="__main__":
    port=int(os.getenv("PORT","8001")); print(f"Campaign Content QA: http://localhost:{port}"); ThreadingHTTPServer(("127.0.0.1",port),Handler).serve_forever()
