from pathlib import Path
from datetime import datetime
import shutil


# Get main project directory
ROOT = Path(__file__).resolve().parent.parent


# Original database
DATABASE_FILE = (
    ROOT
    / "database"
    / "mandapam.db"
)


# Backup directory
BACKUP_DIRECTORY = (
    ROOT
    / "database"
    / "backups"
)


# Create backup folder if it does not exist
BACKUP_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)


# Check whether database exists
if not DATABASE_FILE.exists():

    print(
        "Database does not exist yet."
    )

    print(
        "Run the Flask application once first."
    )

else:

    # Create timestamp
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    # Create backup filename
    backup_file = (
        BACKUP_DIRECTORY
        / f"mandapam_backup_{timestamp}.db"
    )

    # Copy database
    shutil.copy2(
        DATABASE_FILE,
        backup_file
    )

    print(
        "Database backup created successfully."
    )

    print(
        f"Backup location: {backup_file}"
    )