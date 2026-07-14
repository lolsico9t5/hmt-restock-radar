"""
HMT Restock Radar — Local Server
==================================
Double-click hmt_proxy.bat to start.
Then open your browser and go to:

   http://localhost:8765

That's it. The radar will open and auto-refresh.
"""

import sys, os, urllib.parse

try:
    import requests
except ImportError:
    print("Installing 'requests' library...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8765
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE  = os.path.join(SCRIPT_DIR, "HMT_Restock_Radar_CORRECT.html")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9,ta;q=0.8",
    "Cache-Control": "no-cache",
})

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()

    def do_GET(self):
        # Serve radar HTML at root
        if self.path in ("/", "/index.html"):
            if not os.path.exists(HTML_FILE):
                self._text(404, "HMT_Restock_Radar_CORRECT.html not found in same folder!"); return
            with open(HTML_FILE, "rb") as f: body = f.read()
            self.send_response(200); self._cors()
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body); return

        # Proxy at /fetch?url=TARGET
        if self.path.startswith("/fetch"):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            target = params.get("url",[None])[0]
            if not target or not target.startswith("http"):
                self._text(400,"Bad request"); return
            self._proxy(target); return

        # Legacy: /ENCODED_URL
        target = urllib.parse.unquote(self.path.lstrip("/"))
        if target.startswith("http"):
            self._proxy(target); return

        self._text(404, "Not found")

    def _proxy(self, target):
        print(f"  Fetching: {target}")
        try:
            resp = session.get(target, timeout=20, allow_redirects=True)
            body = resp.content
            self.send_response(resp.status_code); self._cors()
            self.send_header("Content-Type", resp.headers.get("Content-Type","text/html; charset=utf-8"))
            self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body)
            print(f"  OK {resp.status_code} — {len(body):,} bytes")
        except Exception as e:
            print(f"  ERR {e}"); self._text(502, str(e))

    def _text(self, code, msg):
        b = msg.encode()
        self.send_response(code); self._cors()
        self.send_header("Content-Type","text/plain")
        self.send_header("Content-Length", str(len(b))); self.end_headers()
        self.wfile.write(b)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers","*")

    def log_message(self, *a): pass

def main():
    print("=" * 50)
    print("  HMT Restock Radar")
    print("=" * 50)
    print()
    print("  Radar found ✓" if os.path.exists(HTML_FILE) else "  WARNING: HTML file not found in this folder!")
    print()
    print("  Open your browser and go to:")
    print()
    print("     http://localhost:8765")
    print()
    print("  Keep this window open.")
    print("  Press Ctrl+C to stop.")
    print("-" * 50)
    HTTPServer(("localhost", PORT), Handler).serve_forever()

if __name__ == "__main__":
    main()
