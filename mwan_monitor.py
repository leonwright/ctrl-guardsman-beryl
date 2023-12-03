import sqlite3
import subprocess
import datetime
import yaml
import logging

# Load configuration from YAML file
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

config = load_config('config.yml')

# Set up logging
logging.basicConfig(level=logging.INFO)

# Database configuration
db_path = config['sqlite']['mwan3_path']  # Update this with the path to your SQLite database

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

    now = datetime.datetime.now()
    cursor.execute("INSERT OR REPLACE INTO mwan3_status (interface_name, is_online, last_online_time, last_checked_time) "
                   "VALUES (?, ?, ?, ?)",
                   (interface_name, is_online, now if is_online else None, now))

    connection.commit()
    cursor.close()
    connection.close()

# Parse interface status
interface_statuses = parse_interface_status()

# Update database for each interface
for interface, status in interface_statuses.items():
    update_database(interface, status)

print("Database updated successfully.")