# Battery Lab — Teacher's Guide (2 hours)

A hands-on lab where students see a small but complete client/server stack:
a Tkinter GUI talks to a Python TCP server that reads/writes a SQLite
database of batteries.

Everything is **standard library only**. No `pip install`. Tested with
Python 3.10+.

---

## 0. Before class (you, the teacher)

1. Push this folder to a Git host the students can reach (GitHub, Gitea,
   your school's GitLab, etc.).
2. Confirm every student PC has Python 3 with the **py launcher** (the
   default Windows installer from python.org provides this and includes
   Tkinter and sqlite3 — nothing extra to install).
   - Quick test from `cmd`: `py -3 -c "import tkinter, sqlite3; print('ok')"`
3. Make sure no firewall on the student machines blocks **localhost** TCP
   (port 5050). The server only binds to 127.0.0.1 — no inbound network
   permission is needed.

## 1. Student quickstart (put this on the board)

```
git clone <your-repo-url>
cd <repo-folder>

1) double-click  setup.bat        (one time — creates batteries.db)
2) double-click  run_server.bat   (leave this window open)
3) double-click  run_client.bat   (the GUI)
```

If the GUI says "Connection failed", the server window isn't running yet.

---

## 2. The architecture (5-minute whiteboard)

```
   +----------------+      JSON over TCP       +----------------+      SQL      +-------------+
   |  client.py     |  <-------------------->  |  server.py     |  <--------->  | batteries.db|
   |  (Tkinter GUI) |    127.0.0.1:5050        |  (sockets)     |               | (SQLite)    |
   +----------------+                          +----------------+               +-------------+
```

Three layers, three responsibilities:

- **Database** — knows facts. Doesn't know about users.
- **Server** — knows the rules. Translates requests into SQL, returns rows.
  Hides the database from clients.
- **Client** — knows the user. Renders, accepts input, sends requests.

Why split it? Many clients can talk to one server. The server is the only
process that ever opens the DB file. Tomorrow we could replace Tkinter
with a web page or a phone app — the server doesn't care.

---

## 3. Pacing (2 hours)

### 0:00 – 0:10 — Welcome & demo
- Run `setup.bat`, `run_server.bat`, `run_client.bat` on the projector.
- Click **Show all**, type `Li-ion` in Chemistry, click **Search**, then
  **Stats**. Show the server console printing each request.

### 0:10 – 0:20 — Whiteboard the architecture
- The diagram above.
- Ask: *"What happens between clicking Search and seeing rows?"* Walk the
  signal path: button → JSON → socket → SQL → SQLite → rows → JSON → tree.

### 0:20 – 0:35 — Read the code together (10 min/file, in this order)
1. **`seed_db.py`** — schema, sample rows, `executemany`. Point out
   `INTEGER PRIMARY KEY AUTOINCREMENT` and that the SQL lives in a string.
2. **`server.py`** — show `socket.bind/listen/accept`, the `for raw in f`
   read loop, and how `handle_request` dispatches on `action`. Highlight
   the **parameterized queries** (`?` placeholders) and ask *why* — they
   prevent SQL injection.
3. **`client.py`** — start at `BatteryClient.call`: write JSON + `\n`,
   read one line, parse. Then look at how buttons in `_build_ui` call
   `self.client.call(...)`.

### 0:35 – 0:50 — Talk to the server *without* the GUI
Open a third terminal and run this one-liner; great "aha" moment:

```bash
py -3 -c "import socket,json; s=socket.create_connection(('127.0.0.1',5050)); s.sendall(b'{\"action\":\"stats\"}\n'); print(s.makefile('rb').readline().decode())"
```

Or have students write `query.py`:

```python
import socket, json
s = socket.create_connection(("127.0.0.1", 5050))
f = s.makefile("rwb")
f.write(b'{"action":"search","chemistry":"Li-ion"}\n'); f.flush()
print(json.loads(f.readline()))
```

Drives the point home: the GUI is just *one* client.

### 0:50 – 1:00 — Break

### 1:00 – 1:35 — Exercise A (pick one — pair students up)

**A1. Add an `update` action.**
- In `server.py`, add an `if action == "update":` branch using
  `UPDATE batteries SET ... WHERE id = ?`.
- In `client.py`, add an "Edit selected..." button that opens a dialog
  pre-filled from the selected row.
- *Hint:* you can copy `AddDialog` and tweak it.

**A2. Add a new column `country_of_origin TEXT`.**
- Edit the schema in `seed_db.py`, re-run `setup.bat`.
- Add it to `COLUMNS` in `server.py` and to `App.COLS` in `client.py`.
- Add a country field to the Add dialog.
- *Discussion:* in a real system you can't just drop the table —
  introduces the idea of **migrations**.

**A3. Sort by capacity (descending) when a checkbox is ticked.**
- Add a parameter `sort_by` to the `list`/`search` actions on the server.
- Whitelist allowed values (`id`, `capacity_mah`, `voltage_v`) — never
  paste user input directly into SQL. Why? **SQL injection.**

### 1:35 – 1:50 — Exercise B: two clients, one server
- Have student X add a battery from their GUI.
- Have student Y on the same machine click **Show all**.
- They see X's row. Discuss: the server is the single source of truth.
- Optional: change `HOST = "0.0.0.0"` in `server.py` and connect from a
  neighbour's PC by IP. Discuss why production servers need **auth** and
  **TLS** before exposing a port.

### 1:50 – 2:00 — Wrap-up & Q&A
Talking points to close:
- We used `?` placeholders → safe from SQL injection. Why string-concat
  would be unsafe.
- JSON-line is a tiny, hand-rolled protocol. HTTP/REST is the same idea
  with more conventions (verbs, status codes, headers).
- One thread per connection is fine for a class; production servers use
  thread pools, async I/O, or processes.
- Where would *you* add login? Where would you add caching?

---

## 4. Common student issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `py is not recognized` | Python not installed, or "Add to PATH" was unchecked | Reinstall Python from python.org with both checkboxes ticked |
| Client window flashes "Connection failed" | Server isn't running, or `setup.bat` was skipped | Run `setup.bat`, then `run_server.bat`, then `run_client.bat` |
| `OSError: [WinError 10048] ... only one usage` | Server already running in another window | Close the other server window, or change `PORT` in both `server.py` and `client.py` |
| `batteries.db not found` | They started the server before seeding | Run `setup.bat` |
| GUI shows old data after editing the DB by hand | Client cached nothing — but a query may have been cached on tree | Click **Show all** |

---

## 5. Cheat sheet — protocol reference

All requests and responses are a single JSON object on one line.

| Request                                                    | Response                          |
|------------------------------------------------------------|-----------------------------------|
| `{"action":"list"}`                                        | `{"ok":true,"rows":[...]}`        |
| `{"action":"search","chemistry":"Li-ion","min_capacity":3000}` | `{"ok":true,"rows":[...]}`    |
| `{"action":"add","data":{"name":"...","chemistry":"NiMH",...}}` | `{"ok":true,"id":21}`        |
| `{"action":"delete","id":21}`                              | `{"ok":true,"deleted":1}`         |
| `{"action":"stats"}`                                       | `{"ok":true,"rows":[...]}`        |

Errors always come back as `{"ok": false, "error": "..."}`.

---

## 6. Files in this lab

- `seed_db.py` — creates `batteries.db` and inserts ~20 sample rows.
- `server.py`  — TCP server on `127.0.0.1:5050`.
- `client.py`  — Tkinter GUI client.
- `setup.bat`, `run_server.bat`, `run_client.bat` — Windows launchers.
- `TEACHER.md` — this file.

Good luck — and may your students leave understanding that "client/server"
is not magic, just two programs that agreed on a protocol.
