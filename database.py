import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "phone_search.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    email TEXT
);
"""

SAMPLE_DATA = [
    ("+12025550101", "Alice Johnson", "123 Main St", "Washington", "DC", "alice.johnson@example.com"),
    ("+12025550102", "Bob Smith", "456 Oak Ave", "Washington", "DC", "bob.smith@example.com"),
    ("+13105550171", "Carol Williams", "789 Pine Rd", "Los Angeles", "CA", "carol.w@example.com"),
    ("+13105550172", "David Brown", "321 Elm St", "Los Angeles", "CA", "david.b@example.com"),
    ("+16175550193", "Eva Martinez", "654 Maple Dr", "Boston", "MA", "eva.m@example.com"),
    ("+16175550194", "Frank Garcia", "987 Cedar Ln", "Boston", "MA", "frank.g@example.com"),
    ("+17135550187", "Grace Lee", "135 Birch Blvd", "Houston", "TX", "grace.l@example.com"),
    ("+17135550188", "Henry Wilson", "246 Walnut Way", "Houston", "TX", "henry.w@example.com"),
    ("+16025550131", "Irene Taylor", "357 Spruce St", "Phoenix", "AZ", "irene.t@example.com"),
    ("+16025550132", "Jack Anderson", "468 Willow Ave", "Phoenix", "AZ", "jack.a@example.com"),
]


def get_connection(db_path=None):
    """Return a sqlite3 connection to the database."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None):
    """Create tables and populate sample data if not already present."""
    conn = get_connection(db_path)
    with conn:
        conn.execute(SCHEMA)
        for row in SAMPLE_DATA:
            conn.execute(
                "INSERT OR IGNORE INTO contacts (phone, name, address, city, state, email) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                row,
            )
    conn.close()


def lookup_phone(phone: str, db_path=None):
    """
    Look up a contact by their E.164 phone number.
    Returns a dict with contact details or None if not found.
    """
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT name, phone, address, city, state, email FROM contacts WHERE phone = ?",
            (phone,),
        ).fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()
