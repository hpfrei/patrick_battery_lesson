"""HTTP server: serves the web UI and a JSON API over batteries.db.

Endpoints
---------
GET    /                      → index.html (the web UI)
GET    /api/batteries         → list rows; optional query params:
                                  chemistry, form_factor, manufacturer, min_capacity
POST   /api/batteries         → add a row (JSON body)
DELETE /api/batteries/<id>    → delete a row
GET    /api/stats             → row counts and averages grouped by chemistry

Run:
    py -3 server.py        (Windows)
    python3 server.py      (Linux/macOS)

The DB is auto-created from seed_db.py on first run.
A browser tab opens automatically.
"""

import http.server
import json
import os
import re
import socketserver
import sqlite3
import urllib.parse
import webbrowser

HOST = "127.0.0.1"
PORT = 5050
HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "batteries.db")
INDEX_PATH = os.path.join(HERE, "index.html")

COLUMNS = [
    "id", "name", "manufacturer", "chemistry", "form_factor",
    "capacity_mah", "voltage_v", "weight_g", "rechargeable",
    "year_introduced", "notes",
]


def db_exec(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.execute(sql, params)
        rows = cur.fetchall()
        con.commit()
        return rows, cur.lastrowid, cur.rowcount
    finally:
        con.close()


def list_batteries(qs):
    clauses, params = [], []
    for field in ("chemistry", "form_factor", "manufacturer"):
        v = (qs.get(field) or [""])[0].strip()
        if v:
            clauses.append(f"{field} LIKE ?")
            params.append(f"%{v}%")
    mc = (qs.get("min_capacity") or [""])[0].strip()
    if mc:
        clauses.append("capacity_mah >= ?")
        params.append(int(mc))
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows, _, _ = db_exec(
        f"SELECT {', '.join(COLUMNS)} FROM batteries {where} ORDER BY id",
        params,
    )
    return [dict(zip(COLUMNS, r)) for r in rows]


def add_battery(d):
    _, last, _ = db_exec(
        """INSERT INTO batteries
           (name, manufacturer, chemistry, form_factor, capacity_mah,
            voltage_v, weight_g, rechargeable, year_introduced, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (d.get("name"), d.get("manufacturer"), d.get("chemistry"),
         d.get("form_factor"), d.get("capacity_mah"),
         d.get("voltage_v"), d.get("weight_g"),
         1 if d.get("rechargeable") else 0,
         d.get("year_introduced"), d.get("notes")),
    )
    return last


def delete_battery(rid):
    _, _, n = db_exec("DELETE FROM batteries WHERE id = ?", (rid,))
    return n


def chemistry_stats():
    rows, _, _ = db_exec(
        """SELECT chemistry,
                  COUNT(*),
                  ROUND(AVG(capacity_mah), 1),
                  ROUND(AVG(voltage_v),   2)
           FROM batteries
           GROUP BY chemistry
           ORDER BY COUNT(*) DESC"""
    )
    keys = ["chemistry", "count", "avg_capacity_mah", "avg_voltage_v"]
    return [dict(zip(keys, r)) for r in rows]


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "BatteryLab/2.0"

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, ctype):
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        n = int(self.headers.get("Content-Length", 0))
        if n == 0:
            return {}
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path in ("/", "/index.html"):
            return self._send_file(INDEX_PATH, "text/html; charset=utf-8")
        if url.path == "/api/batteries":
            qs = urllib.parse.parse_qs(url.query)
            return self._send_json(200, {"rows": list_batteries(qs)})
        if url.path == "/api/stats":
            return self._send_json(200, {"rows": chemistry_stats()})
        self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/batteries":
            try:
                data = self._read_json()
            except json.JSONDecodeError as e:
                return self._send_json(400, {"error": f"bad JSON: {e}"})
            if not data.get("name") or not data.get("chemistry"):
                return self._send_json(400, {"error": "name and chemistry are required"})
            try:
                return self._send_json(201, {"id": add_battery(data)})
            except sqlite3.Error as e:
                return self._send_json(400, {"error": f"{type(e).__name__}: {e}"})
        self._send_json(404, {"error": "not found"})

    def do_DELETE(self):
        m = re.match(r"^/api/batteries/(\d+)$", self.path)
        if m:
            n = delete_battery(int(m.group(1)))
            return self._send_json(200, {"deleted": n})
        self._send_json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {self.address_string()} {fmt % args}")


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def ensure_db():
    if not os.path.exists(DB_PATH):
        print(f"[server] {os.path.basename(DB_PATH)} not found — seeding...")
        import seed_db
        seed_db.main()


def main():
    ensure_db()
    httpd = ThreadingServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"[server] listening on {url}  (Ctrl+C to stop)")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] shutting down")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
