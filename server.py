"""TCP server: exposes batteries.db via a JSON-line protocol.

Wire format
-----------
Client opens a TCP connection. For each request it sends one JSON object
followed by a newline. The server responds with one JSON object followed
by a newline. The connection stays open for more requests.

Each connected client is handled in its own thread.

Run:
    py server.py          (listens on 127.0.0.1:5050)
"""

import json
import os
import socket
import sqlite3
import threading

HOST = "127.0.0.1"
PORT = 5050
DB_PATH = os.path.join(os.path.dirname(__file__), "batteries.db")

COLUMNS = [
    "id", "name", "manufacturer", "chemistry", "form_factor",
    "capacity_mah", "voltage_v", "weight_g", "rechargeable",
    "year_introduced", "notes",
]


def row_to_dict(row):
    return {c: row[i] for i, c in enumerate(COLUMNS)}


def handle_request(req):
    """Dispatch one request dict to SQL, return a response dict."""
    action = req.get("action")
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()

        if action == "list":
            cur.execute(f"SELECT {', '.join(COLUMNS)} FROM batteries ORDER BY id")
            return {"ok": True, "rows": [row_to_dict(r) for r in cur.fetchall()]}

        if action == "search":
            clauses, params = [], []
            for field in ("chemistry", "form_factor", "manufacturer"):
                if req.get(field):
                    clauses.append(f"{field} LIKE ?")
                    params.append(f"%{req[field]}%")
            if req.get("min_capacity") is not None:
                clauses.append("capacity_mah >= ?")
                params.append(int(req["min_capacity"]))
            where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
            cur.execute(
                f"SELECT {', '.join(COLUMNS)} FROM batteries {where} ORDER BY id",
                params,
            )
            return {"ok": True, "rows": [row_to_dict(r) for r in cur.fetchall()]}

        if action == "add":
            d = req.get("data", {})
            cur.execute(
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
            con.commit()
            return {"ok": True, "id": cur.lastrowid}

        if action == "delete":
            cur.execute("DELETE FROM batteries WHERE id = ?", (int(req["id"]),))
            con.commit()
            return {"ok": True, "deleted": cur.rowcount}

        if action == "stats":
            cur.execute(
                """SELECT chemistry,
                          COUNT(*)                    AS n,
                          ROUND(AVG(capacity_mah), 1) AS avg_mah,
                          ROUND(AVG(voltage_v), 2)    AS avg_v
                   FROM batteries
                   GROUP BY chemistry
                   ORDER BY n DESC"""
            )
            keys = ["chemistry", "count", "avg_capacity_mah", "avg_voltage_v"]
            return {"ok": True, "rows": [dict(zip(keys, r)) for r in cur.fetchall()]}

        return {"ok": False, "error": f"unknown action: {action!r}"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        con.close()


def serve_client(conn, addr):
    print(f"[server] {addr} connected")
    f = conn.makefile("rwb")
    try:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                req = json.loads(raw)
            except json.JSONDecodeError as e:
                resp = {"ok": False, "error": f"bad JSON: {e}"}
            else:
                print(f"[server] {addr} -> {req}")
                resp = handle_request(req)
            f.write((json.dumps(resp) + "\n").encode("utf-8"))
            f.flush()
    except (ConnectionError, OSError):
        pass
    finally:
        conn.close()
        print(f"[server] {addr} disconnected")


def main():
    if not os.path.exists(DB_PATH):
        raise SystemExit("batteries.db not found. Run 'py seed_db.py' first.")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"[server] listening on {HOST}:{PORT}  (Ctrl+C to stop)")
    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=serve_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[server] shutting down")
    finally:
        s.close()


if __name__ == "__main__":
    main()
