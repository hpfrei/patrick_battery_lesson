# Battery Lab

A 2-hour Python teaching lab. A **Tkinter GUI client** talks to a **TCP
server** that reads and writes a **SQLite** database of batteries.

Standard library only — **no `pip install` needed**.

![architecture](https://img.shields.io/badge/stack-Python%20%7C%20sockets%20%7C%20SQLite%20%7C%20Tkinter-blue)

```
+----------------+    JSON / TCP    +----------------+    SQL    +-------------+
|  client.py     |  <------------>  |  server.py     |  <----->  | batteries.db|
|  (Tkinter GUI) |  127.0.0.1:5050  |  (sockets)     |           |   (SQLite)  |
+----------------+                  +----------------+           +-------------+
```

Teachers: see [`TEACHER.md`](TEACHER.md) for the lesson plan, pacing, and
exercises.

---

## Install on Linux

Most distros ship Python 3 already, but on Debian/Ubuntu the Tkinter
module is a separate package.

```bash
# Debian / Ubuntu / WSL
sudo apt update
sudo apt install -y python3 python3-tk git

# Fedora
sudo dnf install -y python3 python3-tkinter git

# Arch
sudo pacman -S --needed python tk git
```

Verify:

```bash
python3 -c "import tkinter, sqlite3; print('ok')"
```

Clone and run:

```bash
git clone https://github.com/hpfrei/patrick_battery_lesson.git
cd patrick_battery_lesson

./setup.sh        # one-time DB seed
./run_server.sh   # leave this terminal open
./run_client.sh   # in a second terminal
```

> WSL note: WSLg (Windows 11 / recent Windows 10) renders the Tk window
> automatically. On older WSL you need an X server (e.g. VcXsrv) and
> `export DISPLAY=:0`.

---

## Install on Windows

### 1. Install Python

1. Go to <https://www.python.org/downloads/windows/> and download the
   latest **Python 3** installer (64-bit).
2. Run the installer. **Important — tick both checkboxes** on the first
   screen:
   - ☑ **Add python.exe to PATH**
   - ☑ **Use admin privileges when installing py.exe**
3. Click **Install Now** (the default selection installs Tkinter and
   sqlite3 — exactly what we need).

Verify the install: open **Command Prompt** (`Win` + `R`, type `cmd`,
Enter) and run:

```
py -3 --version
py -3 -c "import tkinter, sqlite3; print('ok')"
```

You should see `Python 3.x.x` and then `ok`. If either line errors,
re-run the installer and tick the boxes above.

### 2. Install Git

1. Download Git for Windows from <https://git-scm.com/download/win>.
2. Run the installer; the defaults are fine.

Verify: in Command Prompt, run `git --version`.

### 3. Clone this repo

In Command Prompt, `cd` to where you want the project and run:

```
git clone https://github.com/hpfrei/patrick_battery_lesson.git
cd patrick_battery_lesson
```

---

## Run it

Run these **in this order**:

| #  | Windows           | Linux               | What it does                                         |
|----|-------------------|---------------------|------------------------------------------------------|
| 1  | `setup.bat`       | `./setup.sh`        | Creates `batteries.db` and loads 20 sample rows. **Run this once.** |
| 2  | `run_server.bat`  | `./run_server.sh`   | Starts the server. **Leave this window open** while you use the app. |
| 3  | `run_client.bat`  | `./run_client.sh`   | Opens the GUI. You can run this multiple times for multiple clients. |

On Windows you can double-click the `.bat` files from File Explorer.

When you are done, close the GUI window and press `Ctrl+C` in the server
window (or just close it).

---

## What the GUI can do

- **Show all** — list every battery in the database.
- **Search** — filter by chemistry, form factor, and minimum capacity (mAh).
- **Add battery...** — insert a new row via a dialog.
- **Delete selected** — remove the highlighted row.
- **Stats** — count and average capacity/voltage grouped by chemistry.

The status bar at the bottom shows row counts and any errors.

---

## Talk to the server without the GUI

The server speaks a tiny line-based JSON protocol. Try this from any
Python prompt while `run_server.bat` is running:

```python
import socket, json
s = socket.create_connection(("127.0.0.1", 5050))
f = s.makefile("rwb")
f.write(b'{"action":"stats"}\n'); f.flush()
print(json.loads(f.readline()))
```

Supported actions: `list`, `search`, `add`, `delete`, `stats`. See
`TEACHER.md` for the full protocol reference.

---

## Troubleshooting

| Problem                                   | Fix                                                                 |
|-------------------------------------------|---------------------------------------------------------------------|
| `'py' is not recognized`                  | Reinstall Python and tick **Add python.exe to PATH**.               |
| GUI says **Connection failed**            | `run_server.bat` is not running yet. Start it first.                |
| `batteries.db not found`                  | Run `setup.bat` once before starting the server.                    |
| Server: `WinError 10048 ... only one usage` | Another server is already on port 5050 — close that window.       |
| `'git' is not recognized`                 | Install Git for Windows (see step 2 above).                         |

---

## Files

```
seed_db.py        Creates batteries.db and inserts 20 sample rows
server.py         TCP server on 127.0.0.1:5050, JSON-line protocol
client.py         Tkinter GUI client
setup.bat / setup.sh             Runs seed_db.py
run_server.bat / run_server.sh   Runs server.py
run_client.bat / run_client.sh   Runs client.py
TEACHER.md        2-hour lesson plan with exercises
README.md         You are here
```
