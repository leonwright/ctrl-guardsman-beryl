import sqlite3
import subprocess
import datetime
import yaml
import logging

# Load configuration from YAML file
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

config = load_config('/root/ctrl-guardsman-beryl/config.yml')

# Set up logging
logging.basicConfig(level=logging.INFO)

# Database configuration
db_path = config['sqlite']['mwan3_path']

# Function to parse interface status
def parse_interface_status():
    result = subprocess.run(['mwan3', 'interfaces'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    status_dict = {}
    for line in lines:
        if 'interface' in line:
            parts = line.split()
            interface_name = parts[1].replace('is', '').strip()
            is_online = 'online' in line
            status_dict[interface_name] = is_online
    return status_dict

# Function to update database
def update_database(interface_name, is_online):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Create or update the table structure
    cursor.execute("CREATE TABLE IF NOT EXISTS mwan3_status ("
                   "interface_name TEXT PRIMARY KEY, "
                   "is_online INTEGER, "
                   "last_online_time TEXT, "
                   "last_checked_time TEXT, "
                   "last_power_cycle_time TEXT)")

    now = datetime.datetime.now()

    cursor.execute("SELECT last_online_time, last_power_cycle_time FROM mwan3_status WHERE interface_name = ?", (interface_name,))
    record = cursor.fetchone()
    last_online_time = record[0] if record else None
    last_power_cycle_time = record[1] if record else None

    if is_online:
        cursor.execute("INSERT OR REPLACE INTO mwan3_status (interface_name, is_online, last_online_time, last_checked_time, last_power_cycle_time) "
                       "VALUES (?, ?, ?, ?, ?)",
                       (interface_name, is_online, now, now, last_power_cycle_time))
    else:
        cursor.execute("INSERT OR REPLACE INTO mwan3_status (interface_name, is_online, last_online_time, last_checked_time, last_power_cycle_time) "
                       "VALUES (?, ?, ?, ?, ?)",
                       (interface_name, is_online, last_online_time, now, last_power_cycle_time))

    connection.commit()
    cursor.close()
    connection.close()

# Parse interface status
interface_statuses = parse_interface_status()

# Update database for each interface
for interface, status in interface_statuses.items():
    update_database(interface, status)

# Output a snapshot of the database
def print_database_snapshot():
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM mwan3_status")
    snapshot = cursor.fetchall()
    print("Database snapshot:")
    for row in snapshot:
        print(row)
    cursor.close()
    connection.close()

print_database_snapshot()

print("Database updated successfully.")
