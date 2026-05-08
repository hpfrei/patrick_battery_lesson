"""Create batteries.db and populate it with sample data.

Run this once before starting the server. Re-running resets the database.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "batteries.db")

SCHEMA = """
CREATE TABLE batteries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    manufacturer    TEXT,
    chemistry       TEXT    NOT NULL,
    form_factor     TEXT,
    capacity_mah    INTEGER,
    voltage_v       REAL,
    weight_g        REAL,
    rechargeable    INTEGER NOT NULL DEFAULT 0,
    year_introduced INTEGER,
    notes           TEXT
);
"""

# name, manufacturer, chemistry, form_factor, mAh, V, g, rechargeable, year, notes
SAMPLE = [
    ("Energizer MAX AA",        "Energizer",  "Alkaline",   "AA",        2850,  1.5,    23.0, 0, 1980, "Common single-use household cell"),
    ("Duracell Coppertop AAA",  "Duracell",   "Alkaline",   "AAA",       1200,  1.5,    11.5, 0, 1985, "Single-use AAA"),
    ("Eneloop Pro AA",          "Panasonic",  "NiMH",       "AA",        2550,  1.2,    30.0, 1, 2013, "Low self-discharge rechargeable"),
    ("Eneloop AAA",             "Panasonic",  "NiMH",       "AAA",        950,  1.2,    13.0, 1, 2005, "Low self-discharge rechargeable"),
    ("Samsung 30Q",             "Samsung",    "Li-ion",     "18650",     3000,  3.7,    45.0, 1, 2014, "High-drain 18650 cell"),
    ("LG HG2",                  "LG Chem",    "Li-ion",     "18650",     3000,  3.7,    47.0, 1, 2014, "Popular vape/EV cell"),
    ("Molicel P42A",            "Molicel",    "Li-ion",     "21700",     4000,  3.7,    70.0, 1, 2019, "High-power 21700"),
    ("Tesla 4680",              "Tesla",      "Li-ion",     "4680",      9000,  3.7,   355.0, 1, 2020, "Large-format EV cell"),
    ("CR2032",                  "Various",    "Lithium",    "Coin",       225,  3.0,     3.0, 0, 1977, "Coin cell for watches and key fobs"),
    ("CR123A",                  "Various",    "Lithium",    "CR123A",    1500,  3.0,    17.0, 0, 1985, "Camera and flashlight primary"),
    ("9V Block",                "Duracell",   "Alkaline",   "9V",         565,  9.0,    46.0, 0, 1956, "Smoke alarms, multimeters"),
    ("Optima YellowTop",        "Optima",     "Lead-acid",  "Group 34", 55000, 12.0, 19500.0, 1, 1994, "Deep cycle AGM car battery"),
    ("Trojan T-105",            "Trojan",     "Lead-acid",  "GC2",     225000,  6.0, 28000.0, 1, 1952, "Golf cart flooded cell"),
    ("BYD Blade",               "BYD",        "LiFePO4",    "Prismatic",202000, 3.2,  2500.0, 1, 2020, "EV traction battery cell"),
    ("Headway 38120",           "Headway",    "LiFePO4",    "38120",    10000,  3.2,   320.0, 1, 2010, "Cylindrical LFP for solar/EV"),
    ("Apple iPhone 15 cell",    "Apple",      "Li-ion",     "Pouch",     3349,  3.87,   48.0, 1, 2023, "Smartphone pouch cell"),
    ("Bosch ProCore 18V 8.0Ah", "Bosch",      "Li-ion",     "Pack",      8000, 18.0,  1300.0, 1, 2019, "Power-tool pack (5x21700)"),
    ("Varta Silver Dynamic H8", "Varta",      "Lead-acid",  "H8",       80000, 12.0, 22500.0, 1, 2002, "Car SLI battery"),
    ("Zinc-Carbon AA",          "GP",         "Zinc-carbon","AA",         600,  1.5,    17.0, 0, 1898, "Cheapest AA chemistry, low capacity"),
    ("Saft LSH20",              "Saft",       "Li-SOCl2",   "D",        13000,  3.6,   100.0, 0, 1985, "Long-life industrial lithium primary"),
]


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(SCHEMA)
    cur.executemany(
        """INSERT INTO batteries
           (name, manufacturer, chemistry, form_factor, capacity_mah,
            voltage_v, weight_g, rechargeable, year_introduced, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        SAMPLE,
    )
    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM batteries").fetchone()[0]
    con.close()
    print(f"Created {DB_PATH} with {n} rows.")


if __name__ == "__main__":
    main()
