import sqlite3
import yaml
import logging
from datetime import datetime
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
    connection = sqlite3.connect(config['sqlite']['ping_path'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM PingResults")
    rows = cursor.fetchall()
    connection.close()
    return rows

def format_data_for_influx(rows):
    influx_data = []
    for row in rows:
        point = Point("ping_metrics") \
            .tag("server_ip", row[1]) \
            .tag("location_name", config['location_name']) \
            .field("min_latency", float(row[3])) \
            .field("max_latency", float(row[4])) \
            .field("avg_latency", float(row[5])) \
            .field("success_rate", float(row[6])) \
            .time(datetime.strptime(row[7], '%Y-%m-%d %H:%M:%S'))
        influx_data.append(point)
    return influx_data

def upload_to_influx(data):
    with InfluxDBClient(url=config['influx_db']['url'],
                        token=config['influx_db']['token'],
                        org=config['influx_db']['org']) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=config['influx_db']['bucket'], record=data)

def clear_database():
    connection = sqlite3.connect(config['sqlite']['iperf_path'])
    cursor = connection.cursor()
    cursor.execute("DELETE FROM PingResults")
    connection.commit()
    connection.close()

def main():
    dry_run = config['dry_run']

    rows = fetch_data()
    if rows:
        influx_data = format_data_for_influx(rows)
        if not dry_run:
            upload_to_influx(influx_data)
            clear_database()
            logging.info("Data uploaded to InfluxDB.")
        else:
            logging.info(f"Dry run: Data prepared for upload: {influx_data}")
    else:
        logging.info("No new data to upload.")

if __name__ == "__main__":
    main()
