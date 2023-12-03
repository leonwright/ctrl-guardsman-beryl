import mwan3
import json

def main():
  # Example usage:
  w = mwan3.Mwan3Wrapper()

  status = json.loads("{'interfaces': {'interface wan': {'online_status': 'offline and tracking', 'time_online': 'down', 'uptime': '', 'tracking_status': ''}, 'interface wwan': {'online_status': 'offline and tracking', 'time_online': 'down', 'uptime': '', 'tracking_status': ''}, 'interface tethering': {'online_status': 'offline and tracking', 'time_online': 'down', 'uptime': '', 'tracking_status': ''}, 'interface wan6': {'online_status': 'offline and tracking', 'time_online': 'down', 'uptime': '', 'tracking_status': ''}, 'interface wwan6': {'online_status': 'offline and tracking', 'time_online': 'down', 'uptime': '', 'tracking_status': ''}, 'interface tethering6': {'online_status': 'offline and tracking', 'time_online': 'down', 'uptime': '', 'tracking_status': ''}, 'interface WAN10': {'online_status': 'online 133h:45m:11s', 'time_online': 'uptime 136h:16m:52s and tracking', 'uptime': 'active', 'tracking_status': ''}, 'interface WAN20': {'online_status': 'online 07h:04m:13s', 'time_online': 'uptime 100h:16m:44s and tracking', 'uptime': 'active', 'tracking_status': ''}, 'interface WAN30': {'online_status': 'online 02h:11m:26s', 'time_online': 'uptime 136h:16m:44s and tracking', 'uptime': 'active', 'tracking_status': ''}, 'interface WAN40': {'online_status': 'online 03h:02m:35s', 'time_online': 'uptime 136h:16m:48s and tracking', 'uptime': 'active', 'tracking_status': ''\}\}")
  extract_interface_status(status, 'WAN10')
  extract_interface_status(status, 'WAN20')
  extract_interface_status(status, 'WAN30')
  extract_interface_status(status, 'WAN40')
  print(status)

def extract_interface_status(json_data, interface_name):
  interface_info = json_data.get('interfaces', {})

  # Extracting the interface name and online status
  for name, details in interface_info.items():
    # Cleaning up the interface name
    cleaned_name = name.replace('interface ', '').upper()

    if cleaned_name == interface_name:
      # Determining the online status
      online_status = details.get('online_status')
      status = 'online' if 'online' in online_status else 'offline'
      return status

  return 'unknown'

if __name__ == "__main__":
  main()
