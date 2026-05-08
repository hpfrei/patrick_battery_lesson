"""HTTP server: serves the shop UI and a JSON API over shop.db.

Endpoints
---------
GET    /                      → index.html (the web UI)

GET    /api/products          → list all products (shop catalog)

POST   /api/orders            → place an order
                                body: {customer_name, customer_email,
                                       customer_address, notes,
                                       items: [{product_id, quantity}, ...]}
GET    /api/orders            → list all orders (admin)
GET    /api/orders/<id>       → one order with its line items
PATCH  /api/orders/<id>       → update status; body: {status: "..."}
DELETE /api/orders/<id>       → delete an order (cascades to items)

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
import webbrowser

HOST = "127.0.0.1"
PORT = 5050
HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "shop.db")
INDEX_PATH = os.path.join(HERE, "index.html")

PRODUCT_COLS = [
    "id", "name", "manufacturer", "chemistry", "form_factor",
    "capacity_mah", "voltage_v", "price_cents", "stock", "description",
]
ORDER_COLS = [
    "id", "customer_name", "customer_email", "customer_address",
    "notes", "total_cents", "status", "created_at",
]
ITEM_COLS = [
    "id", "order_id", "product_id", "product_name",
    "unit_price_cents", "quantity",
]
ALLOWED_STATUS = {"pending", "processing", "shipped", "delivered", "cancelled"}


def connect():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def list_products():
    with connect() as con:
        rows = con.execute(
            f"SELECT {', '.join(PRODUCT_COLS)} FROM products ORDER BY id"
        ).fetchall()
    return [dict(zip(PRODUCT_COLS, r)) for r in rows]


def create_order(d):
    name    = (d.get("customer_name")    or "").strip()
    email   = (d.get("customer_email")   or "").strip()
    address = (d.get("customer_address") or "").strip()
    notes   = (d.get("notes") or "").strip() or None
    items   = d.get("items") or []
    if not name or not email or not address:
        raise ValueError("name, email, and address are required")
    if not items:
        raise ValueError("at least one item is required")

    # Validate quantities and collect product ids
    cleaned = []
    for it in items:
        try:
            pid = int(it["product_id"])
            qty = int(it["quantity"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("each item needs product_id and quantity")
        if qty < 1:
            raise ValueError("quantity must be at least 1")
        cleaned.append((pid, qty))

    with connect() as con:
        # Look up current price + stock for each product (server-side truth)
        ids = [pid for pid, _ in cleaned]
        placeholders = ",".join("?" * len(ids))
        rows = con.execute(
            f"SELECT id, name, price_cents, stock FROM products WHERE id IN ({placeholders})",
            ids,
        ).fetchall()
        by_id = {r[0]: r for r in rows}
        if len(by_id) != len(set(ids)):
            raise ValueError("unknown product in order")

        total = 0
        line_rows = []
        for pid, qty in cleaned:
            _, pname, price, stock = by_id[pid]
            if qty > stock:
                raise ValueError(f"not enough stock for '{pname}' (have {stock})")
            total += price * qty
            line_rows.append((pid, pname, price, qty))

        cur = con.execute(
            """INSERT INTO orders
               (customer_name, customer_email, customer_address,
                notes, total_cents, status)
               VALUES (?, ?, ?, ?, ?, 'pending')""",
            (name, email, address, notes, total),
        )
        order_id = cur.lastrowid
        con.executemany(
            """INSERT INTO order_items
               (order_id, product_id, product_name, unit_price_cents, quantity)
               VALUES (?, ?, ?, ?, ?)""",
            [(order_id, pid, pname, price, qty) for pid, pname, price, qty in line_rows],
        )
        # Decrement stock
        con.executemany(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            [(qty, pid) for pid, _, _, qty in line_rows],
        )
        con.commit()
        return order_id


def list_orders():
    with connect() as con:
        rows = con.execute(
            f"SELECT {', '.join(ORDER_COLS)} FROM orders ORDER BY id DESC"
        ).fetchall()
    return [dict(zip(ORDER_COLS, r)) for r in rows]


def get_order(order_id):
    with connect() as con:
        row = con.execute(
            f"SELECT {', '.join(ORDER_COLS)} FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        if not row:
            return None
        order = dict(zip(ORDER_COLS, row))
        items = con.execute(
            f"SELECT {', '.join(ITEM_COLS)} FROM order_items WHERE order_id = ? ORDER BY id",
            (order_id,),
        ).fetchall()
        order["items"] = [dict(zip(ITEM_COLS, r)) for r in items]
        return order


def update_order_status(order_id, status):
    if status not in ALLOWED_STATUS:
        raise ValueError(f"status must be one of {sorted(ALLOWED_STATUS)}")
    with connect() as con:
        cur = con.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id),
        )
        con.commit()
        return cur.rowcount


def delete_order(order_id):
    with connect() as con:
        cur = con.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        con.commit()
        return cur.rowcount


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "BatteryShop/1.0"

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
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            return self._send_file(INDEX_PATH, "text/html; charset=utf-8")
        if path == "/api/products":
            return self._send_json(200, {"rows": list_products()})
        if path == "/api/orders":
            return self._send_json(200, {"rows": list_orders()})
        m = re.match(r"^/api/orders/(\d+)$", path)
        if m:
            order = get_order(int(m.group(1)))
            if order is None:
                return self._send_json(404, {"error": "order not found"})
            return self._send_json(200, order)
        self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/orders":
            try:
                data = self._read_json()
            except json.JSONDecodeError as e:
                return self._send_json(400, {"error": f"bad JSON: {e}"})
            try:
                oid = create_order(data)
                return self._send_json(201, {"id": oid})
            except ValueError as e:
                return self._send_json(400, {"error": str(e)})
            except sqlite3.Error as e:
                return self._send_json(400, {"error": f"{type(e).__name__}: {e}"})
        self._send_json(404, {"error": "not found"})

    def do_PATCH(self):
        m = re.match(r"^/api/orders/(\d+)$", self.path)
        if m:
            try:
                data = self._read_json()
            except json.JSONDecodeError as e:
                return self._send_json(400, {"error": f"bad JSON: {e}"})
            status = (data.get("status") or "").strip()
            try:
                n = update_order_status(int(m.group(1)), status)
            except ValueError as e:
                return self._send_json(400, {"error": str(e)})
            if n == 0:
                return self._send_json(404, {"error": "order not found"})
            return self._send_json(200, {"updated": n})
        self._send_json(404, {"error": "not found"})

    def do_DELETE(self):
        m = re.match(r"^/api/orders/(\d+)$", self.path)
        if m:
            n = delete_order(int(m.group(1)))
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
