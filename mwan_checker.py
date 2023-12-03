import sqlite3
import datetime
import logging
import yaml
import asyncio
from kasa import SmartStrip
import time

# Load configuration from YAML file
def load_config(file_path):
    with open(file_path, 'r') as file:
        logging.debug("Loading configuration file.")
        return yaml.safe_load(file)

print("Loading configuration file.")
config = load_config('/root/ctrl-guardsman-beryl/config.yml')

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Database configuration
db_path = config['sqlite']['mwan3_path']
logging.debug(f"Database path set to {db_path}")

# Function to check if an interface has been offline for more than five minutes
def check_interface_offline(interface_name):
    logging.debug(f"Checking if interface {interface_name} has been offline for more than five minutes.")
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("SELECT last_online_time FROM mwan3_status WHERE interface_name = ?", (interface_name,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()

    if result and result[0]:
        last_online_time = datetime.datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
        now = datetime.datetime.now()
        offline_duration = now - last_online_time
        is_offline = offline_duration.total_seconds() > 300
        logging.debug(f"Interface {interface_name} offline status: {is_offline}")
        return is_offline
    logging.debug(f"No last online time found for interface {interface_name}")
    return False

async def toggle_plug(ip_address, plug_alias, turn_off):
    logging.debug(f"Toggling plug {plug_alias} at {ip_address}. Turn off: {turn_off}")
    # Create a SmartStrip object with the specified IP address
    strip = SmartStrip(ip_address)

    try:
        await strip.update()
        for plug in strip.children:
            if plug.alias == plug_alias:
                if turn_off:
                    await plug.turn_off()
                    logging.info(f"Plug '{plug_alias}' turned OFF.")
                else:
                    await plug.turn_on()
                    logging.info(f"Plug '{plug_alias}' turned ON.")
                return
    except Exception as e:
        logging.error(f"Error connecting to the power strip at {ip_address}: {e}")

async def power_cycle_plug(ip_address, plug_alias):
    logging.info(f"Power cycling plug {plug_alias} at {ip_address}")
    await toggle_plug(ip_address, plug_alias, turn_off=True)
    time.sleep(5)
    await toggle_plug(ip_address, plug_alias, turn_off=False)

# Main routine
async def main():
    for interface in config['interfaces']:
        interface_name = interface['name']
        plug_alias = interface['smartplug_alias']
        if check_interface_offline(interface_name):
            logging.info(f"Interface {interface_name} has been offline for more than five minutes. Power cycling plug {plug_alias}.")
            await power_cycle_plug(config['smart_plug']['ip'], plug_alias)
        else:
            logging.debug(f"Interface {interface_name} is online or no data available.")

if __name__ == "__main__":
    logging.debug("Starting main routine.")
    asyncio.run(main())
