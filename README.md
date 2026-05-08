# Battery Shop

A small **battery shop** web app. A browser talks to a Python HTTP
server that reads and writes a SQLite database of products and orders.
Customers browse, add to cart, and place orders (no payment — orders
are recorded for the shop owner to fulfil). A separate **Admin** tab
lets the shop owner see every order, change its status, and delete it.

Standard library only — **no `pip install` needed**.

```
+------------------+      HTTP       +------------------+      SQL      +-------------+
|  Browser         |  <----------->  |  server.py       |  <--------->  |  shop.db    |
|  (index.html +   |    GET / POST   |  (http.server)   |               |  (SQLite)   |
|   fetch + JS)    |    PATCH/DELETE |                  |               +-------------+
+------------------+                 +------------------+
```

Three views in the UI: **Shop**, **Cart**, **Admin**. The cart lives in
`localStorage` so it survives a refresh.

Teachers/devs: see [`TEACHER.md`](TEACHER.md) for a full walk-through.

---

## Install on Windows

### 1. Install Python

1. Go to <https://www.python.org/downloads/windows/> and download the
   latest **Python 3** installer (64-bit).
2. Run the installer. **Important — tick both checkboxes** on the first
   screen:
   - ☑ **Add python.exe to PATH**
   - ☑ **Use admin privileges when installing py.exe**
3. Click **Install Now**.

Verify in **Command Prompt** (`Win` + `R`, type `cmd`, Enter):

```
py -3 --version
py -3 -c "import http.server, sqlite3; print('ok')"
```

If either errors, re-run the installer with the boxes ticked.

### 2. Install Git

Download from <https://git-scm.com/download/win> and install with
defaults. Verify with `git --version`.

### 3. Clone and run

```
git clone <your-repo-url>
cd <repo-folder>
run.bat
```

Or just double-click `run.bat` from File Explorer. A browser tab opens
automatically at <http://127.0.0.1:5050/>.

---

## Install on Linux

```bash
# Debian / Ubuntu / WSL
sudo apt update
sudo apt install -y python3 git

# Fedora
sudo dnf install -y python3 git

# Arch
sudo pacman -S --needed python git
```

Verify:

```bash
python3 -c "import http.server, sqlite3; print('ok')"
```

Clone and run:

```bash
git clone <your-repo-url>
cd <repo-folder>
./run.sh
```

A browser tab opens automatically.

> WSL note: WSLg (Windows 11 / recent Windows 10) opens the Linux
> browser on your Windows desktop. If `webbrowser.open` does nothing,
> just open <http://127.0.0.1:5050/> manually.

---

## What you can do in the browser

### Shop tab
- Browse the catalogue: every product shows price, stock, chemistry,
  form factor, and a short description.
- Filter by **chemistry**, **form factor**, or free-text **search**.
- Set a quantity, click **Add to cart**.

### Cart tab
- See line items, change quantities, remove items, empty the cart.
- Fill in name, email, address, and an optional note, then click
  **Place order**. No payment — the order is just recorded.

### Admin tab
- See every order, newest first. Each row shows the customer, total,
  and a colour-coded status badge.
- Click a row to expand it and see the line items, address, and notes.
- Change the status from the dropdown:
  `pending → processing → shipped → delivered`, or `cancelled`.
- Delete an order (cascades to its line items).

The server log (in the terminal) shows every request as it happens.

---

## Talk to the server without the browser

The server speaks plain HTTP, so any HTTP client works:

```bash
# List products
curl http://127.0.0.1:5050/api/products

# Place an order
curl -X POST http://127.0.0.1:5050/api/orders \
     -H "Content-Type: application/json" \
     -d '{
           "customer_name":    "Alice",
           "customer_email":   "alice@example.com",
           "customer_address": "1 Battery Lane",
           "notes":            "leave by the door",
           "items": [
             {"product_id": 1, "quantity": 2},
             {"product_id": 5, "quantity": 1}
           ]
         }'

# Admin: list orders, fetch one, update status, delete
curl http://127.0.0.1:5050/api/orders
curl http://127.0.0.1:5050/api/orders/1
curl -X PATCH  http://127.0.0.1:5050/api/orders/1 \
     -H "Content-Type: application/json" \
     -d '{"status":"shipped"}'
curl -X DELETE http://127.0.0.1:5050/api/orders/1
```

See `TEACHER.md` for the full endpoint reference.

---

## Troubleshooting

| Problem                                       | Fix                                                              |
|-----------------------------------------------|------------------------------------------------------------------|
| `'py' is not recognized` (Windows)            | Reinstall Python and tick **Add python.exe to PATH**             |
| `python3: command not found` (Linux)          | `sudo apt install python3` (or your distro's equivalent)         |
| Browser shows "Unable to connect"             | Server isn't running yet — start `run.bat` / `./run.sh`          |
| `Errno 98` / `WinError 10048 ... only one usage` | Port 5050 is busy — close the other process or change `PORT` in `server.py` |
| Edits to `index.html` don't appear            | Browser cache — Ctrl+F5 to hard-reload                           |
| "Out of stock" but you want to test again     | Stop the server, delete `shop.db`, start again — it reseeds      |
| Cart shows old items after a code change      | The cart lives in `localStorage` — open DevTools → Application → Storage → Clear |

---

## Files

```
seed_db.py    Creates shop.db with 12 sample products + empty orders/order_items
server.py     HTTP server on 127.0.0.1:5050 (catalogue + orders + admin API)
index.html    Web UI with Shop / Cart / Admin tabs (HTML + CSS + vanilla JS)
run.bat       Windows launcher (double-clickable)
run.sh        Linux launcher
TEACHER.md    Walkthrough, architecture notes, exercises
README.md     You are here
```
