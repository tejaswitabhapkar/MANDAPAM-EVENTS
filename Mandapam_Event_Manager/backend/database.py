import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash


# Get the main project folder
BASE_DIR = Path(__file__).resolve().parent.parent


# Location of the SQLite database
DB_PATH = BASE_DIR / "database" / "mandapam.db"


def get_db():
    """
    Create and return a connection to the SQLite database.
    """

    # Make sure the database folder exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Connect to SQLite
    connection = sqlite3.connect(DB_PATH)

    # Allow database rows to be accessed using column names
    connection.row_factory = sqlite3.Row

    # Enable foreign-key relationships
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_db():
    """
    Create all required database tables
    and insert initial services/admin account.
    """

    db = get_db()

    # -----------------------------
    # USERS TABLE
    # -----------------------------
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            email TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------
    # SERVICES TABLE
    # -----------------------------
    db.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    """)

    # -----------------------------
    # BOOKINGS TABLE
    # -----------------------------
    db.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT,
            venue TEXT NOT NULL,
            guests INTEGER DEFAULT 0,
            notes TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (service_id)
                REFERENCES services(id)
                ON DELETE CASCADE
        )
    """)

    # -----------------------------
    # FEEDBACK TABLE
    # -----------------------------
    db.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            email TEXT,
            rating TEXT,
            features TEXT,
            improvement TEXT,
            comments TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
        )
    """)

    # -----------------------------
    # DEFAULT SERVICES
    # -----------------------------
    services = [
        (
            "Wedding Planning",
            "Complete wedding planning and coordination."
        ),
        (
            "Birthday Parties",
            "Birthday decoration, games, cake and return gifts."
        ),
        (
            "Corporate Events",
            "Conference setup, audio system, seating and catering."
        ),
        (
            "Concerts & Shows",
            "Stage, lighting, sound, artists and guest management."
        ),
        (
            "Catering Services",
            "Buffet, snacks, menu planning and waiter service."
        ),
        (
            "Photography",
            "Event photography, candid photography and video shoots."
        )
    ]

    for service_name, service_description in services:

        db.execute(
            """
            INSERT OR IGNORE INTO services
            (name, description)
            VALUES (?, ?)
            """,
            (service_name, service_description)
        )

    # -----------------------------
    # DEFAULT ADMIN ACCOUNT
    # -----------------------------

    admin_phone = "9999999999"

    admin = db.execute(
        """
        SELECT id
        FROM users
        WHERE phone = ?
        """,
        (admin_phone,)
    ).fetchone()

    admin_password = generate_password_hash("Admin@123")

    if admin is None:

        db.execute(
            """
            INSERT INTO users
            (name, phone, email, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Mandapam Admin",
                admin_phone,
                "admin@mandapam.local",
                admin_password,
                "admin"
            )
        )

    else:

        db.execute(
            """
            UPDATE users
            SET name = ?,
                email = ?,
                password_hash = ?,
                role = ?
            WHERE phone = ?
            """,
            (
                "Mandapam Admin",
                "admin@mandapam.local",
                admin_password,
                "admin",
                admin_phone
            )
        )

    # Save changes
    db.commit()

    # Close database
    db.close()