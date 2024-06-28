import re
import requests
import schedule
import time
import datetime
import pytz
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Function ############################################################################


def read_mdstat_file(file_path) -> str:
    """Read the content of the mdstat file."""
    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
        exit(1)


def send_discord_notification(url, message_object) -> None:
    """Send a message to a Discord Webhook."""
    response = requests.post(url, json=message_object)

    try:
        response.raise_for_status()

    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print(f"Payload delivered successfully, code {response.status_code}.")


def get_match(mdstat_content, pattern) -> list:
    """Search for the match in the mdstat file."""
    matches = re.findall(pattern, mdstat_content)
    if matches:
        return matches
    else:
        return None


def discord_factory(matchs) -> dict:
    """Create a discord message from the match."""
    # Create root message object
    message = {
        "content": "RAID report: ",
        "embeds": []
    }

    for match in matchs:
        # Get the content of the match
        mountPoint, raidState, raidType, disksList, total, other, diskState, other2 = match

        # Get failed disk
        disks = disksList.split(" ")
        failedDisks = []
        for index, char in enumerate(diskState):
            if char == "_":
                failedDisks.append(disks[index])

        # Create the embed object
        embed = {}

        # Change the message according to the type
        if failedDisks:
            message["content"] = message["content"] + f"{mountPoint}  :x: "
            embed["title"] = f"{mountPoint}  :x:"
            embed["description"] = f"Failed disks: {', '.join(failedDisks)}"
            embed["color"] = 16063773
        else:
            message["content"] = message["content"] + f"{mountPoint} :white_check_mark: "
            embed["title"] = f"{mountPoint} RAID status :white_check_mark:"
            embed["description"] = "All disks are operational !"
            embed["color"] = 3126294

        # Add the informations
        embed["fields"] = [
            {
                "name": "RAID type",
                "value": raidType,
                "inline": True
            },
            {
                "name": "RAID state",
                "value": raidState,
                "inline": True
            },
            {
                "name": "Disks list",
                "value": ', '.join(disks),
                "inline": False
            },
            {
                "name": "Total",
                "value": total,
                "inline": False
            }
        ]

        # Add footer
        embed["footer"] = {
            "text": "CheckMyRaid report"
        }

        # Add timestamp
        embed["timestamp"] = datetime.datetime.now().isoformat()

        # Add the embed to the message
        message["embeds"].append(embed)

    return message


def is_all_disks_ok(matchs) -> bool:
    """Check if all disks are OK."""
    for match in matchs:
        # Get the content of the match
        mountPoint, raidState, raidType, disksList, total, other, diskState, other2 = match

        # Check if diskState contains "_"
        if "_" in diskState:
            return False

    return True


def main():

    # Variables
    mdstat_file = "/app/data/mdstat"
    discord_url = os.getenv('DISCORD_WEBHOOK_URL')

    # Read the content of the mdstat file
    mdstat_content = read_mdstat_file(mdstat_file)

    # ReGex pattern
    pattern = r"(\w+) : (\w+) (raid\d+) (.+)\n +(\d+) (.+) \[\d+\/\d+\] \[([U_]+)\]\n + \w+: \d+\/\d+ (.+)"

    # Search for the match in the mdstat file
    matches = get_match(mdstat_content, pattern)

    # Get status of the RAID
    raids_status = is_all_disks_ok(matches)

    # Generate the message
    discord_message = discord_factory(matches)

    if raids_status:
        print("RAID status: OK")
    else:
        print("RAID status: KO")

    # Send the notification
    send_discord_notification(discord_url, discord_message)


#######################################################################################
# Start the script 1 time on launch
main()

# Get the timezone and the schedule time
timezone = os.getenv('TZ', 'UTC')
trigerAt = os.getenv('TRIGER_SCHEDULE_AT')

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
    time.sleep(1)
