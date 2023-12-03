import subprocess
import re

class Mwan3Wrapper:
    def __init__(self):
        self.mwan3_command = "mwan3"

    def _run_command(self, command):
        try:
            result = subprocess.run([self.mwan3_command] + command.split(),
                                    capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return e.stderr

    def status(self):
        raw_output = self._run_command("status")
        return self._parse_status(raw_output)

    def _parse_status(self, raw_output):
        sections = raw_output.split("\n\n")
        status_dict = {
            "interfaces": self._parse_interface_status(sections[0]),
            "Current ipv4 policies": self._parse_policies(sections[1]),
            "Current ipv6 policies": self._parse_policies(sections[2]),
            "Directly connected ipv4 networks": self._parse_networks(sections[3]),
            "Directly connected ipv6 networks": self._parse_networks(sections[4]),
            "Active ipv4 user rules": self._parse_rules(sections[5]),
            "Active ipv6 user rules": self._parse_rules(sections[6])
        }
        return status_dict

    def _parse_interface_status(self, section):
        status_lines = section.split("\n")[1:]  # Skip the first line (title)
        interface_status = {}
        for line in status_lines:
            parts = re.split(r' is |\, ', line)
            interface_name = parts[0].strip()
            online_status = parts[1].strip() if len(parts) > 1 else ""
            time_online = parts[2].strip() if len(parts) > 2 else ""
            uptime = parts[3].strip() if len(parts) > 3 else ""
            tracking_status = parts[4].strip() if len(parts) > 4 else ""

            interface_status[interface_name] = {
                "online_status": online_status,
                "time_online": time_online,
                "uptime": uptime,
                "tracking_status": tracking_status
            }
        return interface_status

    def _parse_policies(self, section):
        lines = section.split("\n")[1:]  # Skip the first line (title)
        policies = {}
        current_policy = None
        for line in lines:
            if line.endswith(":"):
                current_policy = line[:-1]
                policies[current_policy] = []
            else:
                policies[current_policy].append(line.strip())
        return policies

    def _parse_networks(self, section):
        return section.split("\n")[1:]  # Skip the first line (title)

    def _parse_rules(self, section):
        return section.split("\n")[1:]  # Skip the first line (title)
