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
    # ------------------------------------------------------------------ #
    # Las Vegas, NV  (702 / 725)
    # ------------------------------------------------------------------ #
    (
        "+17026002101", "Samantha Cruz", 33, "Cell", "T-Mobile",
        "10 Fremont St", "Las Vegas", "NV", "89101",
        "samantha.cruz@example.com",
        "Casino Host", "Golden Gate Casino",
        0, None, None,
        "Diego Cruz",
        "facebook.com/samantha.cruz", None,
        55,
    ),
    (
        "+17026002102", "Marcus Bell", 41, "Cell", "AT&T",
        "220 Las Vegas Blvd", "Las Vegas", "NV", "89102",
        "marcus.bell@example.com",
        "Security Officer", "MGM Grand",
        0, None, "+17026009900",
        "Tina Bell",
        None, "linkedin.com/in/marcusbell",
        30,
    ),
    (
        "+17026002103", "Priya Patel", 27, "Cell", "Verizon",
        "505 Desert Rose Dr", "Henderson", "NV", "89002",
        "priya.patel@example.com",
        "Accountant", "Nevada CPA Group",
        0, None, None,
        "Raj Patel, Anita Patel",
        "facebook.com/priya.patel", "linkedin.com/in/priyapatel",
        18,
    ),
    (
        "+17256002101", "Luis Morales", 38, "Cell", "T-Mobile",
        "88 Sunset Blvd", "Las Vegas", "NV", "89103",
        "luis.morales@example.com",
        "Chef", "Aria Resort",
        0, None, None,
        "Carmen Morales",
        None, None,
        22,
    ),
    (
        "+17256002102", "Ashley Turner", 29, "Cell", "AT&T",
        "410 Warm Springs Rd", "Henderson", "NV", "89014",
        "ashley.t@example.com",
        "Dental Hygienist", "Henderson Smiles",
        0, None, None,
        "Mike Turner",
        "facebook.com/ashley.turner", None,
        14,
    ),
    (
        "+17256002103", "Devon Scott", 45, "Landline", "CenturyLink",
        "1300 Boulder Hwy", "Las Vegas", "NV", "89104",
        "devon.scott@example.com",
        "Plumber", "Scott Plumbing LLC",
        0, None, "+17256009811",
        "Janet Scott",
        None, "linkedin.com/in/devonscott",
        9,
    ),
    (
        "+17256002554", "Jordan Lee", 31, "Cell", "Verizon",
        "2100 Sahara Ave", "Las Vegas", "NV", "89104",
        "jordan.lee@example.com",
        "Rideshare Driver", None,
        0, None, None,
        None,
        None, None,
        3,
    ),
    # ------------------------------------------------------------------ #
    # New York, NY  (212 / 646 / 917)
    # ------------------------------------------------------------------ #
    (
        "+12125550201", "Hannah Greene", 36, "Cell", "Verizon",
        "350 5th Ave", "New York", "NY", "10118",
        "hannah.g@example.com",
        "Financial Analyst", "Wall Street Partners",
        0, None, None,
        "Paul Greene, Sophie Greene",
        "facebook.com/hannah.greene", "linkedin.com/in/hannahgreene",
        321,
    ),
    (
        "+12125550202", "Oliver King", 52, "Landline", "Spectrum",
        "99 Park Ave", "New York", "NY", "10016",
        "oliver.king@example.com",
        "Corporate Lawyer", "King & Briggs LLP",
        0, None, "+12125550300",
        "Helen King",
        None, "linkedin.com/in/oliverking",
        88,
    ),
    (
        "+16465550301", "Zoe Mitchell", 24, "Cell", "T-Mobile",
        "75 Bedford St", "New York", "NY", "10014",
        "zoe.m@example.com",
        "Barista", "Brooklyn Roast Coffee",
        0, None, None, None,
        "facebook.com/zoe.mitchell", None,
        41,
    ),
    (
        "+19175550401", "Ethan Brooks", 44, "Cell", "AT&T",
        "500 W 43rd St", "New York", "NY", "10036",
        "ethan.b@example.com",
        "TV Producer", "NBC Studios",
        0, None, "+19175550499",
        "Mia Brooks",
        None, "linkedin.com/in/ethanbrooks",
        73,
    ),
    # ------------------------------------------------------------------ #
    # Chicago, IL  (312 / 773)
    # ------------------------------------------------------------------ #
    (
        "+13125550501", "Maya Richardson", 39, "Cell", "AT&T",
        "233 S Wacker Dr", "Chicago", "IL", "60606",
        "maya.r@example.com",
        "Architect", "Skyline Design Group",
        0, None, None,
        "Lena Richardson",
        "facebook.com/maya.richardson", "linkedin.com/in/mayarichardson",
        110,
    ),
    (
        "+17735550601", "Jake Evans", 28, "Cell", "Sprint",
        "1800 N Milwaukee Ave", "Chicago", "IL", "60647",
        "jake.e@example.com",
        "Bartender", "The Green Mill",
        0, None, None, None,
        "facebook.com/jake.evans", None,
        37,
    ),
    # ------------------------------------------------------------------ #
    # Houston, TX  (713 / 832)
    # ------------------------------------------------------------------ #
    (
        "+17135550701", "Nicole Owens", 47, "Cell", "Verizon",
        "3400 Montrose Blvd", "Houston", "TX", "77006",
        "nicole.o@example.com",
        "Petroleum Engineer", "Gulf Energy Corp",
        0, None, None,
        "Chris Owens, Taylor Owens",
        None, "linkedin.com/in/nicoleowens",
        65,
    ),
    (
        "+18325550801", "Marcus Reyes", 34, "Cell", "T-Mobile",
        "10200 Westheimer Rd", "Houston", "TX", "77042",
        "marcus.r@example.com",
        "Software Developer", "Houston Tech Co",
        0, None, "+18325550899",
        "Alicia Reyes",
        "facebook.com/marcus.reyes", "linkedin.com/in/marcusreyes",
        48,
    ),
    # ------------------------------------------------------------------ #
    # Austin, TX  (512)
    # ------------------------------------------------------------------ #
    (
        "+15125550901", "Chloe Nguyen", 31, "Cell", "AT&T",
        "600 Congress Ave", "Austin", "TX", "78701",
        "chloe.n@example.com",
        "UX Designer", "Austin Digital Labs",
        0, None, None,
        "Tran Nguyen",
        "facebook.com/chloe.nguyen", "linkedin.com/in/chloenguyen",
        93,
    ),
    # ------------------------------------------------------------------ #
    # Dallas, TX  (214 / 469)
    # ------------------------------------------------------------------ #
    (
        "+12145551001", "Brandon White", 50, "Landline", "AT&T",
        "2400 Commerce St", "Dallas", "TX", "75201",
        "brandon.w@example.com",
        "Insurance Broker", "White Risk Advisors",
        0, None, "+12145551099",
        "Sarah White",
        None, "linkedin.com/in/brandonwhite",
        55,
    ),
    (
        "+14695551101", "Amber Hall", 26, "Cell", "Verizon",
        "9090 N Central Expy", "Dallas", "TX", "75231",
        "amber.h@example.com",
        "Pharmacy Tech", "CVS Pharmacy",
        0, None, None, None,
        "facebook.com/amber.hall", None,
        21,
    ),
    # ------------------------------------------------------------------ #
    # Phoenix / Scottsdale, AZ  (480 / 602)
    # ------------------------------------------------------------------ #
    (
        "+14805551201", "Ryan Foster", 37, "Cell", "T-Mobile",
        "7001 N Scottsdale Rd", "Scottsdale", "AZ", "85253",
        "ryan.f@example.com",
        "Real Estate Agent", "Desert Realty",
        0, None, None,
        "Lauren Foster",
        "facebook.com/ryan.foster", "linkedin.com/in/ryanfoster",
        82,
    ),
    (
        "+16025551301", "Diana Ross", 43, "Cell", "AT&T",
        "401 W Van Buren St", "Phoenix", "AZ", "85003",
        "diana.r@example.com",
        "Nurse", "Banner University Medical",
        0, None, None,
        "Kevin Ross",
        None, None,
        44,
    ),
    # ------------------------------------------------------------------ #
    # San Diego, CA  (619 / 858)
    # ------------------------------------------------------------------ #
    (
        "+16195551401", "Tyler Bennett", 29, "Cell", "Verizon",
        "500 Harbor Dr", "San Diego", "CA", "92101",
        "tyler.b@example.com",
        "Marine Biologist", "Scripps Institution",
        0, None, None,
        "Chris Bennett",
        "facebook.com/tyler.bennett", "linkedin.com/in/tylerbennett",
        60,
    ),
    (
        "+18585551501", "Natalie Chen", 35, "Cell", "T-Mobile",
        "9500 Gilman Dr", "La Jolla", "CA", "92093",
        "natalie.c@example.com",
        "Professor", "UC San Diego",
        0, None, None,
        "Wei Chen",
        None, "linkedin.com/in/nataliechen",
        77,
    ),
    # ------------------------------------------------------------------ #
    # San Francisco / Silicon Valley, CA  (415 / 650)
    # ------------------------------------------------------------------ #
    (
        "+14155551601", "Lucas Kim", 32, "Cell", "AT&T",
        "1 Market St", "San Francisco", "CA", "94105",
        "lucas.k@example.com",
        "Product Manager", "TechBridge Inc",
        0, None, "+14155551699",
        "Jenny Kim",
        None, "linkedin.com/in/lucaskim",
        134,
    ),
    (
        "+16505551701", "Sara Pham", 27, "Cell", "T-Mobile",
        "2000 Sand Hill Rd", "Menlo Park", "CA", "94025",
        "sara.p@example.com",
        "Venture Analyst", "Sequoia Capital",
        0, None, None, None,
        None, "linkedin.com/in/sarapham",
        50,
    ),
    # ------------------------------------------------------------------ #
    # Seattle, WA  (206)
    # ------------------------------------------------------------------ #
    (
        "+12065551801", "Aaron Price", 41, "Cell", "Verizon",
        "400 Pike St", "Seattle", "WA", "98101",
        "aaron.p@example.com",
        "Software Engineer", "Amazon",
        0, None, None,
        "Pam Price",
        "facebook.com/aaron.price", "linkedin.com/in/aaronprice",
        201,
    ),
    # ------------------------------------------------------------------ #
    # Portland, OR  (503)
    # ------------------------------------------------------------------ #
    (
        "+15035551901", "Emma Walsh", 30, "Cell", "Sprint",
        "1100 SW 6th Ave", "Portland", "OR", "97204",
        "emma.w@example.com",
        "Graphic Designer", "Willamette Creative Co",
        0, None, None,
        "Brian Walsh",
        "facebook.com/emma.walsh", None,
        29,
    ),
    # ------------------------------------------------------------------ #
    # Denver, CO  (303 / 720)
    # ------------------------------------------------------------------ #
    (
        "+13035552001", "Nathan Reed", 46, "Cell", "AT&T",
        "1700 Lincoln St", "Denver", "CO", "80203",
        "nathan.r@example.com",
        "Civil Engineer", "Rocky Mountain Infrastructure",
        0, None, None,
        "Kelly Reed",
        None, "linkedin.com/in/nathanreed",
        57,
    ),
    (
        "+17205552101", "Olivia Barnes", 25, "Cell", "T-Mobile",
        "8000 E Colfax Ave", "Aurora", "CO", "80010",
        "olivia.b@example.com",
        "Yoga Instructor", None,
        0, None, None, None,
        "facebook.com/olivia.barnes", None,
        12,
    ),
    # ------------------------------------------------------------------ #
    # Atlanta, GA  (404 / 678)
    # ------------------------------------------------------------------ #
    (
        "+14045552201", "Isaiah Carter", 38, "Cell", "Verizon",
        "191 Peachtree St NE", "Atlanta", "GA", "30303",
        "isaiah.c@example.com",
        "Marketing Manager", "Coca-Cola Company",
        0, None, None,
        "Denise Carter",
        "facebook.com/isaiah.carter", "linkedin.com/in/isaiahcarter",
        115,
    ),
    (
        "+16785552301", "Jasmine Howard", 33, "Cell", "AT&T",
        "650 Ponce De Leon Ave NE", "Atlanta", "GA", "30308",
        "jasmine.h@example.com",
        "Pediatrician", "Emory Healthcare",
        0, None, None,
        "Troy Howard",
        None, "linkedin.com/in/jasminehoward",
        44,
    ),
    # ------------------------------------------------------------------ #
    # Miami, FL  (305 / 786)
    # ------------------------------------------------------------------ #
    (
        "+13055552401", "Carlos Mendez", 42, "Cell", "T-Mobile",
        "800 Brickell Ave", "Miami", "FL", "33131",
        "carlos.m@example.com",
        "Financial Advisor", "Brickell Wealth Mgmt",
        0, None, "+13055552499",
        "Rosa Mendez",
        None, "linkedin.com/in/carlosmendez",
        89,
    ),
    (
        "+17865552501", "Valentina Cruz", 28, "Cell", "Verizon",
        "3500 Main Hwy", "Coconut Grove", "FL", "33133",
        "valentina.c@example.com",
        "Fashion Designer", None,
        0, None, None,
        "Marco Cruz",
        "facebook.com/valentina.cruz", None,
        33,
    ),
    # ------------------------------------------------------------------ #
    # Philadelphia, PA  (215 / 267)
    # ------------------------------------------------------------------ #
    (
        "+12155552601", "Daniel Murphy", 55, "Landline", "Comcast",
        "1500 Market St", "Philadelphia", "PA", "19102",
        "daniel.m@example.com",
        "Senior Attorney", "Murphy & Kane LLP",
        0, None, "+12155552699",
        "Mary Murphy",
        None, "linkedin.com/in/danielmurphy",
        70,
    ),
    (
        "+12675552701", "Sophia Adams", 23, "Cell", "AT&T",
        "3600 Chestnut St", "Philadelphia", "PA", "19104",
        "sophia.a@example.com",
        "Graduate Student", "University of Pennsylvania",
        0, None, None, None,
        "facebook.com/sophia.adams", None,
        8,
    ),
    # ------------------------------------------------------------------ #
    # Baltimore, MD  (410 / 443)
    # ------------------------------------------------------------------ #
    (
        "+14435552801", "Derrick Fleming", 49, "Cell", "Verizon",
        "100 Light St", "Baltimore", "MD", "21202",
        "derrick.f@example.com",
        "Harbor Pilot", "Port of Baltimore",
        0, None, None,
        "Lisa Fleming",
        None, None,
        26,
    ),
    # ------------------------------------------------------------------ #
    # Nashville, TN  (615)
    # ------------------------------------------------------------------ #
    (
        "+16155552901", "Chelsea Morgan", 31, "Cell", "AT&T",
        "417 Broadway", "Nashville", "TN", "37203",
        "chelsea.m@example.com",
        "Singer-Songwriter", None,
        0, None, None, None,
        "facebook.com/chelsea.morgan", None,
        67,
    ),
    # ------------------------------------------------------------------ #
    # Minneapolis, MN  (612 / 651)
    # ------------------------------------------------------------------ #
    (
        "+16125553001", "Andrew Larson", 44, "Cell", "T-Mobile",
        "225 S 6th St", "Minneapolis", "MN", "55402",
        "andrew.l@example.com",
        "Software Architect", "Target Corporation",
        0, None, None,
        "Karen Larson",
        None, "linkedin.com/in/andrewlarson",
        48,
    ),
    # ------------------------------------------------------------------ #
    # Detroit, MI  (313)
    # ------------------------------------------------------------------ #
    (
        "+13135553101", "Jamal Washington", 37, "Cell", "Verizon",
        "1 Woodward Ave", "Detroit", "MI", "48226",
        "jamal.w@example.com",
        "Automotive Engineer", "Ford Motor Company",
        0, None, "+13135553199",
        "Aisha Washington",
        None, "linkedin.com/in/jamalwashington",
        53,
    ),
    # ------------------------------------------------------------------ #
    # Columbus, OH  (614)
    # ------------------------------------------------------------------ #
    (
        "+16145553201", "Rachel Green", 28, "Cell", "AT&T",
        "50 W Broad St", "Columbus", "OH", "43215",
        "rachel.g@example.com",
        "Journalist", "Columbus Dispatch",
        0, None, None, None,
        "facebook.com/rachel.green", None,
        19,
    ),
    # ------------------------------------------------------------------ #
    # Indianapolis, IN  (317)
    # ------------------------------------------------------------------ #
    (
        "+13175553301", "Trevor Baker", 53, "Landline", "Comcast",
        "300 N Meridian St", "Indianapolis", "IN", "46204",
        "trevor.b@example.com",
        "Hospital Administrator", "IU Health",
        0, None, None,
        "Donna Baker",
        None, "linkedin.com/in/trevorbaker",
        31,
    ),
    # ------------------------------------------------------------------ #
    # Charlotte, NC  (704 / 980)
    # ------------------------------------------------------------------ #
    (
        "+17045553401", "Monica Jenkins", 40, "Cell", "T-Mobile",
        "500 S Tryon St", "Charlotte", "NC", "28202",
        "monica.j@example.com",
        "Bank Manager", "Bank of America",
        0, None, None,
        "Terrence Jenkins",
        None, "linkedin.com/in/monicajenkins",
        61,
    ),
    # ------------------------------------------------------------------ #
    # San Antonio, TX  (210)
    # ------------------------------------------------------------------ #
    (
        "+12105553501", "Roberto Vasquez", 46, "Cell", "AT&T",
        "300 Alamo Plaza", "San Antonio", "TX", "78205",
        "roberto.v@example.com",
        "Tour Guide", "Alamo Heritage Tours",
        0, None, None,
        "Elena Vasquez",
        "facebook.com/roberto.vasquez", None,
        25,
    ),
    # ------------------------------------------------------------------ #
    # Kansas City, MO  (816)
    # ------------------------------------------------------------------ #
    (
        "+18165553601", "Brianna Cole", 34, "Cell", "Verizon",
        "1 Arrowhead Dr", "Kansas City", "MO", "64129",
        "brianna.c@example.com",
        "Sports Therapist", "KC Chiefs",
        0, None, None,
        "Marcus Cole",
        "facebook.com/brianna.cole", "linkedin.com/in/briannacole",
        40,
    ),
    # ------------------------------------------------------------------ #
    # Additional spam callers / robocallers
    # ------------------------------------------------------------------ #
    (
        "+18555559001", "SPAM CALLER", None, "VoIP", "Unknown",
        None, None, None, None,
        None, None, None,
        88, "Robocaller",
        "+18555559002,+18555559003",
        None, None, None,
        3210,
    ),
    (
        "+13005550100", "SPAM CALLER", None, "VoIP", "Unknown",
        None, None, None, None,
        None, None, None,
        72, "Possible Telemarketer",
        None, None, None, None,
        895,
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
    Increments search_count on each successful lookup.
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
            with conn:
                conn.execute(
                    "UPDATE contacts SET search_count = search_count + 1 WHERE phone = ?",
                    (phone,),
                )
            result = dict(row)
            result["search_count"] = result["search_count"] + 1
            return result
        return None
    finally:
        conn.close()

