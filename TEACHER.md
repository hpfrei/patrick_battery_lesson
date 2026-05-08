# Battery Lab — Teacher's Guide (2 hours)

A hands-on lab where students see a small but complete **web** stack: a
browser talks to a Python **HTTP server** that reads and writes a
**SQLite** database of batteries.

Everything is **standard library only**. No `pip install`, no Flask, no
build tools. Tested with Python 3.10+.

---

## Original brief (what was asked for)

> I want a solution for a teacher to hand out to students for a 2-hour
> session using:
>
> - Python
> - SQLite
> - client/server (web server / web browser)
>
> Topic: **batteries**. Stage the DB with data to play with.
>
> GUI with interactivity.
>
> And a script for the teacher.
>
> Note: students must `git clone` and it must run directly on their
> Windows PCs.

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
The first run creates `batteries.db` and loads 20 sample rows.

---

## 2. The architecture (5-minute whiteboard)

```
   +------------------+      HTTP       +------------------+      SQL      +-------------+
   |  Browser         |  <----------->  |  server.py       |  <--------->  | batteries.db|
   |  (index.html +   |    GET / POST   |  (http.server)   |               |  (SQLite)   |
   |   fetch + JS)    |    DELETE       |                  |               +-------------+
   +------------------+                 +------------------+
```

Three layers, three responsibilities:

- **Database** — knows facts. Doesn't know about HTTP.
- **Server** — knows the rules. Translates URLs and JSON bodies into SQL,
  returns JSON or HTML. The only process that ever opens the DB file.
- **Client** — the *browser*. Renders HTML, accepts input, fires
  `fetch()` calls. Could be replaced by `curl`, by a phone app, by
  another script — the server doesn't care.

This is the same architecture as Twitter, GitHub, Gmail — just smaller.

---

## 3. Pacing (2 hours)

### 0:00 – 0:10 — Welcome & demo
- Run `run.bat` / `./run.sh` on the projector.
- Browser opens. Type `Li-ion` in Chemistry → Search. Click **Stats**.
- Watch the server console log each request:
  `GET /api/batteries?chemistry=Li-ion HTTP/1.1 200 -`

### 0:10 – 0:20 — Whiteboard the architecture
- The diagram above.
- Ask: *"What happens between clicking Search and seeing rows?"* Walk
  the signal path: button → JS `fetch` → HTTP GET → SQL → SQLite → rows
  → JSON → `<table>`.

### 0:20 – 0:35 — Read the code together (5 min/file)
1. **`seed_db.py`** — schema + sample rows. Point out
   `INTEGER PRIMARY KEY AUTOINCREMENT` and `executemany`.
2. **`server.py`** — start at `Handler.do_GET`. Show how a URL maps to a
   function. Then `do_POST` and `do_DELETE`. Highlight the
   **parameterized queries** (`?` placeholders) and ask *why* — they
   prevent SQL injection.
3. **`index.html`** — start at the `loadRows` function. Show how it
   builds a query string, calls `fetch`, parses JSON, builds HTML. The
   buttons in the page just call these JS functions.

### 0:35 – 0:50 — Talk to the server *without* the browser
Open a terminal alongside the running server. The server is just HTTP,
so any HTTP client works:

```bash
# Windows or Linux — curl is built into modern Windows 10/11
curl http://127.0.0.1:5050/api/stats
curl "http://127.0.0.1:5050/api/batteries?chemistry=Li-ion&min_capacity=3000"

curl -X POST http://127.0.0.1:5050/api/batteries ^
     -H "Content-Type: application/json" ^
     -d "{\"name\":\"Test\",\"chemistry\":\"NiMH\",\"capacity_mah\":1500,\"rechargeable\":true}"

curl -X DELETE http://127.0.0.1:5050/api/batteries/21
```

Or from Python:

```python
import urllib.request, json
print(json.loads(urllib.request.urlopen("http://127.0.0.1:5050/api/stats").read()))
```

Drives the point home: **the browser is just one client.** The server
speaks HTTP, and that's a public contract.

### 0:50 – 1:00 — Break

### 1:00 – 1:35 — Exercise A (pick one — pair students up)

**A1. Add a `PUT /api/batteries/<id>` endpoint to update a row.**
- In `server.py`, add `do_PUT`. Use `UPDATE batteries SET ... WHERE id = ?`.
- In `index.html`, add an "Edit" button per row that opens a small form
  pre-filled with the row's values, then `fetch(..., {method: "PUT"})`.

**A2. Add a new column `country_of_origin TEXT`.**
- Edit the schema in `seed_db.py`, delete `batteries.db`, restart.
- Add the column to `COLUMNS` in `server.py` and to the `COLS` array
  and add-form in `index.html`.
- *Discussion:* in a real system you can't just delete the data —
  introduces the idea of **migrations**.

**A3. Add a sort dropdown (capacity / voltage / year).**
- Add `?sort_by=capacity_mah` (and `&sort_dir=desc`) to the list endpoint.
- **Whitelist** allowed values on the server — never paste user input
  directly into SQL. Why? **SQL injection.**

### 1:35 – 1:50 — Exercise B: many clients, one server
- One student adds a battery from their browser.
- A neighbour clicks **Show all** in their browser tab.
- Discuss: the server is the single source of truth.
- Optional, on the same machine: open a second tab, watch the server log
  show two distinct sources hitting the same endpoint.
- Optional, networked: change `HOST = "0.0.0.0"` in `server.py` and have
  a neighbour visit `http://<your-IP>:5050/`. **Stop and discuss**: in
  the real world this is where you'd add **HTTPS** and **authentication**
  before exposing a port.

### 1:50 – 2:00 — Wrap-up & Q&A
Talking points to close:
- We used `?` placeholders → safe from SQL injection. Why string-concat
  would be unsafe.
- HTTP is just a text protocol on top of TCP — no magic. Verbs (GET,
  POST, DELETE), URLs, status codes, headers, optional body. That's it.
- Frameworks like Flask or FastAPI give you routing, validation, and
  templating — same architecture, less hand-rolled boilerplate.
- One thread per request is fine for a class; production servers add
  thread pools, async I/O, reverse proxies (nginx), caching, and
  database connection pools.
- Where would *you* add login? Where would caching help?

---

## 4. Common student issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `'py' is not recognized` (Windows) | Python not installed, or "Add to PATH" was unchecked | Reinstall from python.org with both checkboxes ticked |
| `python3: command not found` (Linux) | Python 3 not installed | `sudo apt install python3` (or your distro's equivalent) |
| Browser shows "Unable to connect" | Server isn't running | Start `run.bat` / `./run.sh`, watch its console for the URL |
| Server: `[Errno 98]` / `WinError 10048` | Another process is on port 5050 | Close it, or change `PORT` in `server.py` |
| Page loads but table is empty | Browser cached an old page | Hard refresh: Ctrl+F5 |
| Edits to `index.html` don't show up | Same — browser cache | Ctrl+F5, or open DevTools → Network → "Disable cache" |
| Stats look wrong after edits | The server is the source of truth — click **Show all** | Or reload the page |

---

## 5. Cheat sheet — HTTP API

| Method | Path                       | Body                       | Returns                        |
|--------|----------------------------|----------------------------|--------------------------------|
| GET    | `/`                        | —                          | `index.html` (the web UI)      |
| GET    | `/api/batteries`           | —                          | `{"rows": [...]}`              |
| GET    | `/api/batteries?chemistry=Li-ion&min_capacity=3000` | — | filtered `{"rows": [...]}` |
| POST   | `/api/batteries`           | `{"name":..., "chemistry":..., ...}` | `201 {"id": 21}`     |
| DELETE | `/api/batteries/21`        | —                          | `{"deleted": 1}`               |
| GET    | `/api/stats`               | —                          | `{"rows": [...]}` (by chemistry) |

Errors come back as `4xx` with `{"error": "..."}` JSON.

---

## 6. Files in this lab

- `seed_db.py`  — creates `batteries.db` and inserts 20 sample rows.
- `server.py`   — HTTP server on `127.0.0.1:5050`.
- `index.html`  — the web UI (HTML + CSS + vanilla JS, single file).
- `run.bat`, `run.sh` — start the server (and open the browser).
- `README.md`   — student-facing install & run instructions.
- `TEACHER.md`  — this file.

Good luck — and may your students leave understanding that "web app" is
not magic, just two programs that agreed on **HTTP**.
