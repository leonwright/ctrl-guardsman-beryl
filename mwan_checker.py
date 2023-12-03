import sqlite3
import datetime
import logging
import yaml

# Load configuration from YAML file
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

config = load_config('/root/ctrl-guardsman-beryl/config.yml')

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Set the logging level to DEBUG for extensive logs

# Database configuration
db_path = config['sqlite']['mwan3_path']  # Update this with the path to your SQLite database

# Function to check if an interface has been offline for more than five minutes
def check_interface_offline(interface_name):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Retrieve the last online time for the interface
    cursor.execute("SELECT last_online_time FROM mwan3_status WHERE interface_name = ?", (interface_name,))
    last_online_time = cursor.fetchone()[0]

    if last_online_time:
        last_online_time = datetime.datetime.strptime(last_online_time, '%Y-%m-%d %H:%M:%S.%f')
        now = datetime.datetime.now()
        offline_duration = now - last_online_time

        if offline_duration.total_seconds() > 300:  # Five minutes in seconds
            logging.debug(f"Interface {interface_name} has been offline for more than five minutes.")
        else:
            logging.debug(f"Interface {interface_name} is online.")

    cursor.close()
    connection.close()

# Specify the interface name you want to check
interface_name = 'WAN40'  # Update this with the interface name you want to check

# Call the function to check the interface status
check_interface_offline(interface_name)
