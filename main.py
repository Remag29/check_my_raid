import re
import sys
from dataclasses import field
from typing import Tuple

import requests
import schedule
import time
import datetime
import pytz
import os
from dotenv import load_dotenv

class Raid:
    def __init__(self, name, disks):
        self.name = name
        self.state = 'KO'
        self.disks = disks
        self.disks_KO = []

    def state_is_good(self) -> None:
        self.state = 'OK'

# Load environment variables from .env file
load_dotenv()

# Function ############################################################################
def parse_raid_file(file_path):
    raids = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
    file.close()

    line_index = 0
    while line_index < len(lines):
        line = lines[line_index].strip()

        # Rechercher la ligne du RAID
        raid_match = re.match(r'^(md\w+)\s*:\s*active\s+raid\d+\s+(.+)', line)
        if raid_match:
            raid = Raid(raid_match.group(1), raid_match.group(2).split())

            # Passe à la ligne suivante pour les blocs et l'état
            line_index += 1
            state_line = lines[line_index].strip()

            # Récupère l'état des disques (ex: [UUUU] pour tous les disques en état)
            state_match = re.search(r'\[([U_]+)\]', state_line)
            if state_match:
                total_disks = len(state_match.group(1))
                good_disks = state_match.group(1).count("U")

                # Vérifier l'état des disques
                if good_disks == total_disks:
                    raid.state_is_good()
                else:
                    for index, disk in enumerate(state_match.group(1)):
                        if disk == "_":
                            raid.disks_KO.append(raid.disks[index])

            raids.append(raid)

        line_index += 1

    return raids


def send_discord_notification(url, message_object) -> None:
    """Send a message to a Discord Webhook."""
    response = requests.post(url, json=message_object)

    try:
        response.raise_for_status()

    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print(f"Payload delivered successfully, code {response.status_code}.")


def discord_factory(raids):
    """Create a discord message from the match."""
    # Create root message object
    problem_detected = None
    message = {
        "content": "All Raids are good.\n---",
        "embeds": []
    }

    # Check if matches is an empty list
    if not raids:
        message["content"] += "No RAID disks found.\n---"
        return message, True

    for raid in raids:
        # Create the embed object
        embed = {}

        # Change the message according to the type
        if raid.state == "KO":
            message["content"] = "A problem has been detected !\n---"
            embed["title"] = f"{raid.name} :x:"
            embed["description"] = f"At least one disks is down"
            embed["color"] = 16063773
            problem_detected = True

        elif raid.state == "OK":
            embed["title"] = f"{raid.name} :white_check_mark:"
            embed["description"] = "All disks are operational !"
            embed["color"] = 3126294
            problem_detected = False

        # Add the information
        embed["fields"] = [
            {
                "name": "RAID state",
                "value": raid.state,
                "inline": True
            },
            {
                "name": "Disks list",
                "value": ', '.join(raid.disks),
                "inline": False
            }
        ]

        if raid.disks_KO:
            embed["fields"].append({
                "name": "Failed disks list",
                "value": ', '.join(raid.disks_KO),
                "inline": False
            })

        # Add footer
        embed["footer"] = {
            "text": "CheckMyRaid report"
        }

        # Add timestamp
        embed["timestamp"] = datetime.datetime.now().isoformat()

        # Add the embed to the message
        message["embeds"].append(embed)

    return message, problem_detected


def main():

    # Variables
    mdstat_file = "/app/data/mdstat"
    discord_url = os.getenv('DISCORD_WEBHOOK_URL')

    # Read the content of the mdstat file
    raids = parse_raid_file(mdstat_file)

    # Generate the message
    discord_message, problem_detected = discord_factory(raids)

    if problem_detected:
        print("Anomalies detected at least on one raid array.")
    else:
        print("All Raids are OK.")

    # Send the notification
    send_discord_notification(discord_url, discord_message)


#######################################################################################
# Start the script 1 time if the variable CHECK_ON_STARTUP is set to True
if os.getenv('CHECK_ON_STARTUP') == "True":
    print("Checking RAID on startup of the container")
    main()

# Get the timezone and the schedule time
timezone = os.getenv('TZ', 'UTC').replace('"', '').replace("'", '')
trigerAt = os.getenv('TRIGER_SCHEDULE_AT', '12:00').replace('"', '').replace("'", '')

# Get the current date and time on the timezone
tz = pytz.timezone(timezone)
now = datetime.datetime.now(tz)

print("Date and time is currently on the timezone",
      timezone, ":", now.strftime("%Y-%m-%d %H:%M:%S"))
print(f"Next raid check scheduled at {trigerAt} \n")

# Schedule the script to run at a specific time
schedule.every().day.at(trigerAt, timezone).do(main)

# Schedule loop
while True:
    schedule.run_pending()
    time.sleep(10)
