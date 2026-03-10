import sqlite3
import os

_DEFAULT_DB = "phone_search.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    phone           TEXT    NOT NULL UNIQUE,
    name            TEXT    NOT NULL,
    age             INTEGER,
    line_type       TEXT,
    carrier         TEXT,
    address         TEXT,
    city            TEXT,
    state           TEXT,
    zip             TEXT,
    email           TEXT,
    job_title       TEXT,
    employer        TEXT,
    spam_score      INTEGER DEFAULT 0,
    spam_label      TEXT,
    other_numbers   TEXT,
    relatives       TEXT,
    social_facebook TEXT,
    social_linkedin TEXT,
    search_count    INTEGER DEFAULT 0
);
"""

SAMPLE_DATA = [
    # (phone, name, age, line_type, carrier, address, city, state, zip, email,
    #  job_title, employer, spam_score, spam_label, other_numbers, relatives,
    #  social_facebook, social_linkedin, search_count)
    (
        "+12025550101", "Alice Johnson", 34, "Cell", "AT&T",
        "123 Main St", "Washington", "DC", "20001",
        "alice.johnson@example.com",
        "Software Engineer", "Tech Corp",
        0, None,
        "+12025550199",
        "Bob Johnson, Carol Johnson",
        "facebook.com/alice.johnson", "linkedin.com/in/alicejohnson",
        142,
    ),
    (
        "+12025550102", "Bob Smith", 47, "Landline", "Verizon",
        "456 Oak Ave", "Washington", "DC", "20002",
        "bob.smith@example.com",
        "Sales Manager", "Metro Solutions",
        0, None,
        None,
        "Diana Smith",
        None, "linkedin.com/in/bobsmith47",
        58,
    ),
    (
        "+13105550171", "Carol Williams", 29, "Cell", "T-Mobile",
        "789 Pine Rd", "Los Angeles", "CA", "90001",
        "carol.w@example.com",
        "Graphic Designer", "Creative Studio LA",
        0, None,
        "+13105550200",
        "Evan Williams, Fiona Williams",
        "facebook.com/carol.williams", None,
        211,
    ),
    (
        "+13105550172", "David Brown", 55, "VoIP", "Google Voice",
        "321 Elm St", "Los Angeles", "CA", "90002",
        "david.b@example.com",
        "Retired", None,
        5, "Possible Robocaller",
        None,
        "Emma Brown",
        None, None,
        980,
    ),
    (
        "+16175550193", "Eva Martinez", 38, "Cell", "T-Mobile",
        "654 Maple Dr", "Boston", "MA", "02101",
        "eva.m@example.com",
        "Nurse Practitioner", "Boston General Hospital",
        0, None,
        None,
        "Luis Martinez, Sofia Martinez",
        "facebook.com/eva.martinez", "linkedin.com/in/evamartinez",
        77,
    ),
    (
        "+16175550194", "Frank Garcia", 62, "Landline", "Comcast",
        "987 Cedar Ln", "Boston", "MA", "02102",
        "frank.g@example.com",
        "Attorney", "Garcia & Associates",
        0, None,
        "+16175550001",
        "Maria Garcia",
        None, "linkedin.com/in/frankgarcia",
        44,
    ),
    (
        "+17135550187", "Grace Lee", 31, "Cell", "Verizon",
        "135 Birch Blvd", "Houston", "TX", "77001",
        "grace.l@example.com",
        "Marketing Analyst", "Gulf Coast Media",
        0, None,
        None,
        "Henry Lee, Irene Lee",
        "facebook.com/grace.lee", "linkedin.com/in/gracelee",
        192,
    ),
    (
        "+17135550188", "Henry Wilson", 44, "Cell", "AT&T",
        "246 Walnut Way", "Houston", "TX", "77002",
        "henry.w@example.com",
        "Electrician", "Wilson Electric",
        0, None,
        "+17135550300",
        "Grace Wilson",
        None, None,
        66,
    ),
    (
        "+16025550131", "Irene Taylor", 26, "Cell", "T-Mobile",
        "357 Spruce St", "Phoenix", "AZ", "85001",
        "irene.t@example.com",
        "Teacher", "Sunridge Elementary",
        0, None,
        None,
        "Jack Taylor, Karen Taylor",
        "facebook.com/irene.taylor", None,
        103,
    ),
    (
        "+16025550132", "Jack Anderson", 50, "Landline", "CenturyLink",
        "468 Willow Ave", "Phoenix", "AZ", "85002",
        "jack.a@example.com",
        "Accountant", "Anderson CPA Group",
        0, None,
        "+16025550400",
        "Linda Anderson",
        None, "linkedin.com/in/jackandersoncpa",
        89,
    ),
    (
        "+18005551234", "SPAM CALLER", None, "VoIP", "Unknown",
        None, None, None, None,
        None, None, None,
        95, "Known Telemarketer",
        "+18005555678,+18005559012",
        None, None, None,
        4521,
    ),
]


def get_connection(db_path=None):
    """Return a sqlite3 connection to the database."""
    path = db_path or os.environ.get("DB_PATH", _DEFAULT_DB)
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
                """INSERT OR IGNORE INTO contacts
                   (phone, name, age, line_type, carrier,
                    address, city, state, zip, email,
                    job_title, employer,
                    spam_score, spam_label,
                    other_numbers, relatives,
                    social_facebook, social_linkedin, search_count)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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
            """SELECT phone, name, age, line_type, carrier,
                      address, city, state, zip, email,
                      job_title, employer,
                      spam_score, spam_label,
                      other_numbers, relatives,
                      social_facebook, social_linkedin, search_count
               FROM contacts WHERE phone = ?""",
            (phone,),
        ).fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

