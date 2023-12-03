import sqlite3
import time
import logging
from datetime import datetime
import yaml
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Load configuration from YAML file
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

config = load_config('config.yml')

# Set up logging
logging.basicConfig(level=logging.INFO)

def fetch_data():
    connection = sqlite3.connect(config['sqlite']['speedtest_path'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM SpeedtestResults")
    rows = cursor.fetchall()
    connection.close()
    return rows

def format_data_for_influx(rows):
    influx_data = []
    for row in rows:
        point = Point("network_metrics") \
            .tag("location_name", config['location_name']) \
            .tag("interface", row[1]) \
            .field("download_speed", float(row[3])) \
            .field("upload_speed", float(row[4])) \
            .field("ping_latency", float(row[5])) \
            .time(datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S'))
        influx_data.append(point)
    return influx_data

def upload_to_influx(data):
    with InfluxDBClient(url=config['influx_db']['url'],
                        token=config['influx_db']['token'],
                        org=config['influx_db']['org']) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=config['influx_db']['bucket'], record=data)

def clear_database():
    connection = sqlite3.connect(config['sqlite']['speedtest_path'])
    cursor = connection.cursor()
    cursor.execute("DELETE FROM SpeedtestResults")
    connection.commit()
    connection.close()

def main():
    dry_run = config['dry_run']
    sleep_interval = config.get('sleep_interval', 60 * 60)  # Default to 1 hour if not specified

    rows = fetch_data()
    if rows:
        influx_data = format_data_for_influx(rows)
        if not dry_run:
            upload_to_influx(influx_data)
            clear_database()
            logging.info("Data uploaded and database cleared.")
        else:
            logging.info(f"Dry run: Data prepared for upload Length: {len(influx_data)}")
    else:
        logging.info("No new data to upload.")

    time.sleep(sleep_interval)

if __name__ == "__main__":
    main()
