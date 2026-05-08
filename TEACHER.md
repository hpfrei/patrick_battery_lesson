# Battery Shop — Walkthrough & Teacher's Guide (2 hours)

A small but complete **web shop** stack: a browser talks to a Python
HTTP server that reads and writes a SQLite database of battery products
and customer orders. Customers add to a cart and place orders (no
payment). A separate admin tab lets the shop owner manage those orders.

Everything is **standard library only**. No `pip install`, no Flask, no
build tools. Tested with Python 3.10+.

---

## Original brief

> Battery shop, no payments — only orders. Orders in a table too. One
> admin tab for the shop admin to manage orders. Same stack as before:
> Python stdlib HTTP server, SQLite, single-file HTML. Must work on
> Windows after `git clone`.

This repo is the deliverable. It also runs on Linux (see `README.md`).

---

## 0. Before class (you, the teacher)

1. Push this folder to a Git host the students can reach.
2. Confirm every student PC has Python 3 (the **py launcher** on Windows;
   `python3` on Linux). The default Windows installer from python.org
   includes everything we need — sqlite3 and the standard library HTTP
   server.
3. Quick test:
   - Windows cmd: `py -3 -c "import http.server, sqlite3; print('ok')"`
   - Linux:       `python3 -c "import http.server, sqlite3; print('ok')"`
4. Make sure students can reach **localhost**. The server binds only to
   127.0.0.1 — no firewall rules needed.

## 1. Student quickstart (put this on the board)

```
git clone <your-repo-url>
cd <repo-folder>

# Windows  → double-click run.bat
# Linux    → ./run.sh
```

A browser tab opens automatically at **http://127.0.0.1:5050/**.
The first run creates `shop.db` and loads 12 sample products.

---

## 2. The architecture (5-minute whiteboard)

```
   +------------------+      HTTP       +------------------+      SQL      +-------------+
   |  Browser         |  <----------->  |  server.py       |  <--------->  |  shop.db    |
   |  (index.html +   |    GET / POST   |  (http.server)   |               |  (SQLite)   |
   |   fetch + JS)    |    PATCH/DELETE |                  |               +-------------+
   +------------------+                 +------------------+
```

Three layers, three responsibilities:

- **Database** — knows facts (products, orders, line items). Doesn't
  know about HTTP.
- **Server** — knows the rules. Translates URLs and JSON bodies into
  SQL, returns JSON or HTML. The only process that ever opens the DB
  file. Owns the **truth** about price and stock — it never trusts
  numbers from the client.
- **Client** — the browser. Renders HTML, accepts input, fires
  `fetch()` calls. The cart is just a JS object kept in `localStorage`;
  it doesn't become "real" until the customer clicks **Place order**.

This is the same architecture as Twitter, GitHub, Gmail — just smaller.

### Three-table data model

```
products                  orders                       order_items
--------                  ------                       -----------
id                        id                           id
name                      customer_name                order_id     ──┐ FK → orders.id (CASCADE)
manufacturer              customer_email               product_id   ──┐ FK → products.id (SET NULL)
chemistry                 customer_address             product_name   ┘  (snapshot — survives delete)
form_factor               notes                        unit_price_cents  (snapshot)
capacity_mah              total_cents                  quantity
voltage_v                 status (pending/.../cancelled)
price_cents               created_at
stock
description
```

Two ideas worth pausing on:

1. **Money in cents (INTEGER), not floats.** Avoids the classic
   `0.1 + 0.2 != 0.3` rounding bugs.
2. **Snapshot price + name on each line item.** When an admin edits a
   product price tomorrow, yesterday's orders still show what the
   customer actually paid. Real shops always do this.

---

## 3. Pacing (2 hours)

### 0:00 – 0:10 — Welcome & demo
- Run `run.bat` / `./run.sh` on the projector.
- Browser opens. Filter by `Li-ion`. Add an item. Switch to the **Cart**
  tab. Fill in name/email/address. Click **Place order**.
- Switch to **Admin**. The new order shows up. Click the row → line
  items expand. Change status to `shipped`.
- Watch the server console log each request:
  `POST /api/orders HTTP/1.1 201 -`, `PATCH /api/orders/1 HTTP/1.1 200 -`.

### 0:10 – 0:20 — Whiteboard the architecture
- Draw the diagram and the three tables above.
- Ask: *"What happens between clicking **Place order** and seeing the
  order in Admin?"* Walk the signal path:
  button → `placeOrder()` → `fetch POST /api/orders` →
  `create_order()` → SQL `INSERT INTO orders`, `INSERT INTO order_items`,
  `UPDATE products SET stock = stock - ?` → JSON `{"id": 1}` → toast.

### 0:20 – 0:35 — Read the code together (5 min/file)
1. **`seed_db.py`** — three `CREATE TABLE`s, `FOREIGN KEY ... CASCADE`,
   `executemany` for the sample products. Note: re-running drops and
   recreates everything.
2. **`server.py`** — start at `Handler.do_POST`. Walk through
   `create_order()`: validate, look up the *real* prices, check stock,
   insert order + items, decrement stock — all inside a single
   transaction (the `with connect()` block). Highlight the
   **parameterized queries** (`?` placeholders) and ask *why* — they
   prevent SQL injection. Then `do_PATCH` (status update,
   server-side allowlist) and `do_DELETE` (cascade).
3. **`index.html`** — three `<section>`s, one shown at a time. Show
   `loadProducts()`, `addToCart()` (just mutates a JS object,
   `localStorage.setItem`), `placeOrder()` (the only client→server
   write), and the admin `loadOrders()` + `setStatus()` pair.

### 0:35 – 0:50 — Talk to the server *without* the browser
Open a terminal alongside the running server. The server is just HTTP,
so any HTTP client works:

```bash
# Browse the catalogue
curl http://127.0.0.1:5050/api/products

# Place an order with curl (no UI involved)
curl -X POST http://127.0.0.1:5050/api/orders ^
     -H "Content-Type: application/json" ^
     -d "{\"customer_name\":\"Bob\",\"customer_email\":\"b@x.com\",\"customer_address\":\"42 Wire St\",\"items\":[{\"product_id\":1,\"quantity\":3}]}"

# Admin: list, inspect, update status, delete
curl http://127.0.0.1:5050/api/orders
curl http://127.0.0.1:5050/api/orders/1
curl -X PATCH  http://127.0.0.1:5050/api/orders/1 -H "Content-Type: application/json" -d "{\"status\":\"shipped\"}"
curl -X DELETE http://127.0.0.1:5050/api/orders/1
```

Or from Python:

```python
import urllib.request, json
print(json.loads(urllib.request.urlopen("http://127.0.0.1:5050/api/products").read()))
```

Drives the point home: **the browser is just one client.** The server
speaks HTTP, and that's a public contract.

Then go one layer deeper: open `shop.db` directly with the `sqlite3`
shell (see §6 for install — it's a single binary on Windows).

```sql
sqlite> .tables
sqlite> SELECT name, stock FROM products WHERE chemistry = 'Li-ion';
```

Same point as before: the server is *one* client of the database, and
SQL is its public contract. §6 has a copy-pasteable list of
catalogue / JOIN / aggregate queries to run during this slot or as
take-home material.

### 0:50 – 1:00 — Break

### 1:00 – 1:35 — Exercise A (pick one — pair students up)

**A1. Add a product-management form to the Admin tab.**
- New endpoints: `POST /api/products`, `PATCH /api/products/<id>`,
  `DELETE /api/products/<id>`.
- New form in the admin section to add or edit a product.
- *Discussion:* who should be allowed to call these? Introduces the
  idea of **authentication** without you having to build it.

**A2. Add an "order confirmation" view.**
- After placing an order, redirect the user to a small page that shows
  `GET /api/orders/<id>` (the response already includes line items).
- *Twist:* exposing every order by id is a problem. Add a random
  `tracking_token` column and require it as `?token=...`. Talk about
  why sequential ids leak information.

**A3. Add a search/filter to the Admin tab.**
- Filter orders by status and by customer email substring.
- Server: `GET /api/orders?status=pending&email=...`
- **Whitelist** allowed status values on the server — never paste user
  input directly into SQL. Why? **SQL injection.**

**A4. "My orders" lookup.**
- A new public tab: enter your email, see your orders.
- Server: `GET /api/orders?email=...` (locked to that email only).
- Discuss why email alone isn't authentication, and how a real shop
  would email a magic link instead.

### 1:35 – 1:50 — Exercise B: many clients, one server
- One student places an order from their browser.
- A neighbour clicks **↻ Refresh** in the Admin tab.
- Discuss: the server is the single source of truth.
- Optional, on the same machine: open two browser windows and watch
  the server log show two distinct sources hitting the same endpoint.
- Optional, networked: change `HOST = "0.0.0.0"` in `server.py` and
  have a neighbour visit `http://<your-IP>:5050/`. **Stop and discuss**:
  in the real world this is where you'd add **HTTPS** and
  **authentication** before exposing a port — and certainly before
  exposing the **Admin** tab.

### 1:50 – 2:00 — Wrap-up & Q&A
Talking points to close:
- We used `?` placeholders → safe from SQL injection.
- The server **never trusts the client's price**. The browser sends
  `{product_id, quantity}` only; the server looks up the real price.
  This is how every real shop avoids people editing JS to pay $0.01.
- Money is stored in **integer cents**, not floats.
- Each order *snapshots* its line items (name + price). Why? Because
  product prices change and orders need to remain a faithful record.
- HTTP is just a text protocol on top of TCP — no magic. Verbs (GET,
  POST, PATCH, DELETE), URLs, status codes, headers, optional body.
- The Admin tab in this lab has **no authentication**. In production
  it'd live behind a login (and HTTPS, and ideally a different domain
  or path) — same architecture, just more layers.
- Frameworks like Flask or FastAPI give you routing, validation, and
  templating — same architecture, less hand-rolled boilerplate.

---

## 4. Common student issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `'py' is not recognized` (Windows) | Python not installed, or "Add to PATH" was unchecked | Reinstall from python.org with both checkboxes ticked |
| `python3: command not found` (Linux) | Python 3 not installed | `sudo apt install python3` (or your distro's equivalent) |
| Browser shows "Unable to connect" | Server isn't running | Start `run.bat` / `./run.sh`, watch its console for the URL |
| Server: `[Errno 98]` / `WinError 10048` | Another process is on port 5050 | Close it, or change `PORT` in `server.py` |
| Cart still has old items after a code change | Cart lives in `localStorage` | DevTools → Application → Storage → Clear, or click **Empty cart** |
| "Out of stock" right after seeding | Stock was decremented by an earlier test | Stop server, delete `shop.db`, start again — it reseeds |
| Edits to `index.html` don't show up | Browser cache | Ctrl+F5, or open DevTools → Network → "Disable cache" |
| Admin shows old orders after a status change | The page only refreshes when you click **↻ Refresh** | Click it, or call `loadOrders()` from the JS console |

---

## 5. Cheat sheet — HTTP API

| Method | Path                  | Body                                                          | Returns                       |
|--------|-----------------------|---------------------------------------------------------------|-------------------------------|
| GET    | `/`                   | —                                                             | `index.html` (the web UI)     |
| GET    | `/api/products`       | —                                                             | `{"rows": [...]}` (catalogue) |
| POST   | `/api/orders`         | `{customer_name, customer_email, customer_address, notes?, items:[{product_id, quantity}]}` | `201 {"id": 1}` |
| GET    | `/api/orders`         | —                                                             | `{"rows": [...]}` (newest first) |
| GET    | `/api/orders/<id>`    | —                                                             | one order with `items:[...]`  |
| PATCH  | `/api/orders/<id>`    | `{"status":"pending|processing|shipped|delivered|cancelled"}` | `{"updated": 1}`              |
| DELETE | `/api/orders/<id>`    | —                                                             | `{"deleted": 1}` (cascades to items) |

Errors come back as `4xx` with `{"error": "..."}` JSON.

---

## 6. Talk to the database directly with SQL

The HTTP server is one client of the database. Students can be another.
Connecting straight to `shop.db` with a SQL prompt makes it visceral
that "the database" is just a file.

> **Heads-up:** SQLite handles concurrent **reads** fine, so
> `SELECT`s while the server is running are safe. For `INSERT` /
> `UPDATE` / `DELETE` it's simpler to **stop the server first** to
> avoid brief lock contention and to make sure the server's view
> doesn't go stale behind the UI.

### Option A — `sqlite3` command-line shell (recommended)

The `sqlite3` CLI is a single binary. **Python's standard library does
not ship it** — you need to install it once.

**Windows** (no admin rights needed):

1. Go to <https://www.sqlite.org/download.html>.
2. Under **Precompiled Binaries for Windows**, download
   `sqlite-tools-win-x64-*.zip`.
3. Unzip it. Inside is `sqlite3.exe`. Drop it into the project folder
   next to `shop.db` (or anywhere on your `PATH`).
4. Open Command Prompt in the project folder and run:

   ```
   sqlite3 shop.db
   ```

**Linux:**

```bash
sudo apt install sqlite3      # Debian / Ubuntu / WSL
sudo dnf install sqlite       # Fedora
sudo pacman -S sqlite         # Arch

sqlite3 shop.db
```

Once at the `sqlite>` prompt, a few useful dot-commands:

```
.tables              -- list tables
.schema products     -- show the CREATE TABLE for one table
.headers on          -- show column headers in query results
.mode column         -- pretty-print as aligned columns
.quit                -- exit
```

### Option B — Python's built-in `sqlite3` module (no install)

Every student already has Python, so this needs zero extra setup.
Python 3.12+ even has an interactive shell built in:

```bash
python -m sqlite3 shop.db        # Python 3.12+
```

On older Pythons, a one-liner works:

```bash
python -c "import sqlite3; [print(r) for r in sqlite3.connect('shop.db').execute('SELECT id, name, price_cents, stock FROM products')]"
```

…or open a regular `python` REPL:

```python
import sqlite3
con = sqlite3.connect("shop.db")
for row in con.execute("SELECT name, stock FROM products ORDER BY stock"):
    print(row)
```

### Option C — DB Browser for SQLite (GUI)

A free cross-platform GUI: <https://sqlitebrowser.org/dl/>.
Open `shop.db` → **Browse Data** tab to click around the rows, or
**Execute SQL** to run queries. Useful for visual learners.

### Queries to try

Drop these into the `sqlite3` prompt one at a time:

```sql
-- 1. The whole catalogue, prettily
SELECT id, name, chemistry, price_cents/100.0 AS price_usd, stock
FROM products
ORDER BY price_cents;

-- 2. What's running low on stock?
SELECT name, stock FROM products WHERE stock < 50 ORDER BY stock;

-- 3. Group by chemistry: how many SKUs and what's the average price?
SELECT chemistry,
       COUNT(*)                             AS sku_count,
       ROUND(AVG(price_cents) / 100.0, 2)   AS avg_price_usd
FROM products
GROUP BY chemistry
ORDER BY sku_count DESC;

-- 4. All orders with a shipped/delivered status, newest first
SELECT id, customer_name, status, total_cents/100.0 AS total_usd, created_at
FROM orders
WHERE status IN ('shipped', 'delivered')
ORDER BY created_at DESC;

-- 5. JOIN: list every line item across every order
SELECT o.id           AS order_id,
       o.customer_name,
       oi.product_name,
       oi.quantity,
       oi.unit_price_cents/100.0 AS unit_price_usd
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
ORDER BY o.id, oi.id;

-- 6. Three-table JOIN: revenue per chemistry
SELECT p.chemistry,
       SUM(oi.unit_price_cents * oi.quantity) / 100.0 AS revenue_usd
FROM order_items oi
JOIN products p ON p.id = oi.product_id
JOIN orders   o ON o.id = oi.order_id
WHERE o.status != 'cancelled'
GROUP BY p.chemistry
ORDER BY revenue_usd DESC;

-- 7. Best-selling product (units sold)
SELECT product_name, SUM(quantity) AS units_sold
FROM order_items
GROUP BY product_name
ORDER BY units_sold DESC
LIMIT 5;
```

Discussion prompts after running these:

- Query 6 joins three tables. Trace each `ON` condition on the
  whiteboard. What would happen if we forgot one of them?
- Query 5 reads `oi.product_name` from `order_items`, **not** from
  `products`. Why was it stored there as a snapshot?
- Try `UPDATE products SET price_cents = 999 WHERE id = 1;` — confirm
  past orders still show the *old* price (they snapshot it). Same
  reason real shops don't retroactively rewrite invoices.

---

## 7. Files in this lab

- `seed_db.py`  — creates `shop.db`: products + orders + order_items.
- `server.py`   — HTTP server on `127.0.0.1:5050`.
- `index.html`  — the web UI with Shop / Cart / Admin tabs (single file).
- `run.bat`, `run.sh` — start the server (and open the browser).
- `README.md`   — student-facing install & run instructions.
- `TEACHER.md`  — this file.

Good luck — and may your students leave understanding that "web shop"
is not magic, just two programs that agreed on **HTTP**.
