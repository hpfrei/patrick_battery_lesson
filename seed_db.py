"""Create shop.db and populate it with sample battery products.

Run this once before starting the server. Re-running resets the database
(products are reset to the sample set; all orders are deleted).
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "shop.db")

SCHEMA = """
CREATE TABLE products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    manufacturer    TEXT,
    chemistry       TEXT    NOT NULL,
    form_factor     TEXT,
    capacity_mah    INTEGER,
    voltage_v       REAL,
    price_cents     INTEGER NOT NULL,
    stock           INTEGER NOT NULL DEFAULT 0,
    description     TEXT
);

CREATE TABLE orders (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name    TEXT    NOT NULL,
    customer_email   TEXT    NOT NULL,
    customer_address TEXT    NOT NULL,
    notes            TEXT,
    total_cents      INTEGER NOT NULL,
    status           TEXT    NOT NULL DEFAULT 'pending',
    created_at       TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id         INTEGER NOT NULL,
    product_id       INTEGER,
    product_name     TEXT    NOT NULL,
    unit_price_cents INTEGER NOT NULL,
    quantity         INTEGER NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);
"""

# name, manufacturer, chemistry, form_factor, mAh, V, price_cents, stock, description
SAMPLE = [
    ("Energizer MAX AA (4-pack)",   "Energizer", "Alkaline",   "AA",      2850,  1.5,   599, 200, "Reliable single-use AA cells. Great for remotes, clocks, toys."),
    ("Duracell Coppertop AAA (8-pk)","Duracell", "Alkaline",   "AAA",     1200,  1.5,   899, 150, "Long-lasting AAA alkalines. Trusted household pick."),
    ("Panasonic Eneloop Pro AA (4)","Panasonic", "NiMH",       "AA",      2550,  1.2,  2199,  80, "High-capacity rechargeables. Pre-charged, 500 cycles."),
    ("Panasonic Eneloop AAA (4)",   "Panasonic", "NiMH",       "AAA",      950,  1.2,  1599,  90, "Low self-discharge AAA rechargeables. 2100 cycles."),
    ("Samsung 30Q 18650",           "Samsung",   "Li-ion",     "18650",   3000,  3.7,   799, 120, "High-drain 18650 cell. Flat top, unprotected."),
    ("LG HG2 18650",                "LG Chem",   "Li-ion",     "18650",   3000,  3.7,   849,  60, "Popular 18650. 20A continuous discharge."),
    ("Molicel P42A 21700",          "Molicel",   "Li-ion",     "21700",   4000,  3.7,  1299,  40, "High-power 21700 cell. 45A continuous."),
    ("Panasonic CR2032 (5-pack)",   "Panasonic", "Lithium",    "Coin",     225,  3.0,   499, 250, "Coin cells for watches, key fobs, motherboards."),
    ("Energizer CR123A (2-pack)",   "Energizer", "Lithium",    "CR123A",  1500,  3.0,  1099, 100, "Camera and tactical flashlight primary cells."),
    ("Duracell 9V Block",           "Duracell",  "Alkaline",   "9V",       565,  9.0,   549, 110, "For smoke alarms and multimeters."),
    ("Headway 38120 LiFePO4",       "Headway",   "LiFePO4",    "38120",  10000,  3.2,  1899,  25, "Cylindrical LFP for solar storage and DIY EV packs."),
    ("Saft LSH20 Lithium D",        "Saft",      "Li-SOCl2",   "D",      13000,  3.6,  2499,  15, "Long-life industrial lithium primary. 10+ year shelf life."),
]


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()
    cur.executescript(SCHEMA)
    cur.executemany(
        """INSERT INTO products
           (name, manufacturer, chemistry, form_factor, capacity_mah,
            voltage_v, price_cents, stock, description)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        SAMPLE,
    )
    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    con.close()
    print(f"Created {DB_PATH} with {n} products.")


if __name__ == "__main__":
    main()
