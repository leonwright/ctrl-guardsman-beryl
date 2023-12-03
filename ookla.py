import sqlite3
import datetime
import json
import logging
import sys
import argparse
from kasa import SmartStrip
import asyncio
import subprocess

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.debug("Logging setup complete.")

# Parse command-line arguments
logging.debug("Parsing command-line arguments.")
parser = argparse.ArgumentParser(description='Internet Connection Monitor Script')
parser.add_argument('--dry-run', action='store_true', help='Run the script in dry run mode (no actual power cycling)')
args = parser.parse_args()
logging.debug(f"Arguments parsed: {args}")

# Load the configuration file
logging.debug("Loading configuration file.")
config_file_path = '/root/plug_script/config.json'
try:
    with open(config_file_path, 'r') as config_file:
        config = json.load(config_file)
        logging.debug(f"Configuration loaded: {config}")
except FileNotFoundError:
    logging.error(f"Configuration file not found at {config_file_path}")
    sys.exit(1)
except Exception as e:
    logging.error("Unexpected error loading configuration file", exc_info=True)
    sys.exit(1)

def check_internet_connection(interface):
    logging.info(f"Checking internet connection for interface: {interface}")
    try:
        start_time = datetime.datetime.now()
        result = subprocess.run(['mwan3', 'status'], capture_output=True, text=True, timeout=10)
        duration = (datetime.datetime.now() - start_time).total_seconds()
        logging.info(f"Command executed in {duration} seconds. Return code: {result.returncode}")

        if result.stdout:
            logging.debug(f"Command stdout: {result.stdout}")
        if result.stderr:
            logging.debug(f"Command stderr: {result.stderr}")

        if result.returncode != 0:
            logging.error(f"mwan3 status command failed with exit code {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        logging.warning(f"Command timed out after 10 seconds. Assuming interface {interface} is offline.")
        return False
    except Exception as e:
        logging.error("Error executing command", exc_info=True)
        return False

    # Parse the command output to find the status of the specified interface
    interface_status_line = next((line for line in result.stdout.split('\n') if line.strip().startswith(f"interface {interface} is")), None)
    if interface_status_line:
        is_online = "online" in interface_status_line
        logging.info(f"Interface {interface} is {'online' if is_online else 'offline'}.")
        return is_online
    else:
        logging.warning(f"Status of interface {interface} not found in mwan3 output.")
        return False

async def power_cycle(strip_ip, socket_index):
    logging.info(f"Initiating power cycle for socket {socket_index} on strip {strip_ip}.")
    try:
        strip = SmartStrip(strip_ip)
        logging.debug("Connecting to smart strip.")
        await strip.update()  # Get the latest status
        logging.debug(f"Strip status updated. Current status: {strip.is_on}")
        socket = strip.children[socket_index]
        logging.debug(f"Socket {socket_index} status: {socket.is_on}")
        await socket.turn_off()
        logging.info(f"Turned off socket {socket_index}.")
        await asyncio.sleep(5)  # Wait for 5 seconds before turning back on
        logging.info("Waiting 5 seconds before turning the socket back on.")
        await socket.turn_on()
        logging.info(f"Turned on socket {socket_index}. Power cycle complete.")
    except Exception as e:
        logging.error(f"Failed to power cycle socket {socket_index} on strip {strip_ip}", exc_info=True)

def main():
    logging.info("Starting main function of the script.")

    # Connect to SQLite database
    db_file = '/root/plug_script/internet_status.db'
    logging.debug(f"Attempting to connect to the database at {db_file}.")
    try:
        conn = sqlite3.connect(db_file)
        logging.info(f"Successfully connected to the database {db_file}.")
    except sqlite3.Error as e:
        logging.error(f"Error connecting to the database {db_file}", exc_info=True)
        sys.exit(1)

    c = conn.cursor()

    # Create table if it doesn't exist
    logging.debug("Creating table 'status' if it doesn't exist.")
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS status
               (interface TEXT PRIMARY KEY, strip_ip TEXT, socket_index INTEGER, last_online DATETIME, last_checked DATETIME)''')
        logging.info("Table 'status' checked/created successfully.")
    except Exception as e:
        logging.error("Error creating/checking table 'status'", exc_info=True)
        conn.close()
        sys.exit(1)

    # Insert or update configuration data
    logging.debug("Inserting/updating configuration data into the database.")
    for interface, details in config['interfaces'].items():
        try:
            c.execute("INSERT OR REPLACE INTO status (interface, strip_ip, socket_index) VALUES (?, ?, ?)",
                  (interface, details['strip_ip'], details['socket_index']))
            logging.info(f"Inserted/updated data for interface: {interface}")
        except Exception as e:
            logging.error(f"Error inserting/updating data for interface: {interface}", exc_info=True)

    conn.commit()
    logging.debug("Database changes committed.")

    # Check the status of each interface
    logging.debug("Checking the status of each interface.")
    try:
        c.execute("SELECT interface, strip_ip, socket_index, last_online, last_checked FROM status")
        interfaces = c.fetchall()
        logging.info(f"Retrieved {len(interfaces)} interfaces from the database.")
    except Exception as e:
        logging.error("Error retrieving interface data", exc_info=True)
        conn.close()
        sys.exit(1)

    for interface, strip_ip, socket_index, last_online, last_checked in interfaces:
        logging.info(f"Processing interface: {interface}")
        is_online = check_internet_connection(interface)

        if is_online:
            logging.debug(f"Interface {interface} is online. Updating last online time.")
            c.execute("UPDATE status SET last_online = ?, last_checked = ? WHERE interface = ?",
                  (datetime.datetime.now(), datetime.datetime.now(), interface))
        else:
            logging.debug(f"Interface {interface} is offline. Updating last checked time.")
            c.execute("UPDATE status SET last_checked = ? WHERE interface = ?",
                  (datetime.datetime.now(), interface))
            logging.debug(f"Last online time: {last_online}")
            if last_online and (datetime.datetime.now() - datetime.datetime.fromisoformat(last_online)).total_seconds() > 300:
                if not args.dry_run:
                    logging.info(f"Initiating power cycle for interface: {interface}")
                    asyncio.run(power_cycle(strip_ip, socket_index))
                else:
                    logging.info(f"Dry run: Would have power cycled socket {socket_index} on strip {strip_ip}.")

    conn.commit()
    logging.info("Final database changes committed.")
    conn.close()
    logging.info("Database connection closed.")
    logging.info("Script execution completed.")

if __name__ == "__main__":
    main()


if __name__ == "__main__":
  main()

