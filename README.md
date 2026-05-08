# Battery Lab

A 2-hour Python teaching lab. A **web browser** talks to a **Python HTTP
server** that reads and writes a **SQLite** database of batteries.

Standard library only — **no `pip install` needed**.

```
+------------------+      HTTP       +------------------+      SQL      +-------------+
|  Browser         |  <----------->  |  server.py       |  <--------->  | batteries.db|
|  (index.html +   |    GET / POST   |  (http.server)   |               |  (SQLite)   |
|   fetch + JS)    |    DELETE       |                  |               +-------------+
+------------------+                 +------------------+
```

Teachers: see [`TEACHER.md`](TEACHER.md) for the lesson plan and
exercises.

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
git clone https://github.com/hpfrei/patrick_battery_lesson.git
cd patrick_battery_lesson
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
git clone https://github.com/hpfrei/patrick_battery_lesson.git
cd patrick_battery_lesson
./run.sh
```

A browser tab opens automatically.

> WSL note: WSLg (Windows 11 / recent Windows 10) opens the Linux
> browser on your Windows desktop. If `webbrowser.open` does nothing,
> just open <http://127.0.0.1:5050/> manually.

---

## What you can do in the browser

- **Search** by chemistry, form factor, and minimum capacity (mAh).
- **Show all** — list every battery.
- **Stats** — counts and averages grouped by chemistry.
- **Add a battery** — fill the form and click Add.
- **Delete** — every row has a delete button.

The server log (in the terminal) shows every request as it happens.

---

## Talk to the server without the browser

The server speaks plain HTTP, so any HTTP client works:

```bash
curl http://127.0.0.1:5050/api/stats
curl "http://127.0.0.1:5050/api/batteries?chemistry=Li-ion&min_capacity=3000"

curl -X POST http://127.0.0.1:5050/api/batteries \
     -H "Content-Type: application/json" \
     -d '{"name":"Test","chemistry":"NiMH","capacity_mah":1500,"rechargeable":true}'

curl -X DELETE http://127.0.0.1:5050/api/batteries/21
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

---

## Files

```
seed_db.py    Creates batteries.db and inserts 20 sample rows
server.py     HTTP server on 127.0.0.1:5050
index.html    Web UI (HTML + CSS + vanilla JS, single file)
run.bat       Windows launcher (double-clickable)
run.sh        Linux launcher
TEACHER.md    2-hour lesson plan with exercises
README.md     You are here
```
