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

def send_ntfy_notification(url, headers, data, auth) -> None:
    """Send an HTTP POST request to trigger a notification on NTFY."""
    response = requests.post(url, headers=headers,
                             data=data.encode('utf-8'), auth=auth)
    if response.status_code == 200:
        print("Notificationn sent successfully.")
    else:
        print("Échec de l'envoi de la notification.")
        print(f"Failed to sent request. Status code: {response.status_code}")

def get_match(mdstat_content, pattern) -> list:
    """Search for the match in the mdstat file."""
    matches = re.findall(pattern, mdstat_content)
    if matches:
        return matches
    else:
        return None

def markdown_factory(matchs) -> str:
    """Create a markdown message from the match."""
    message = "# RAID report\n"

    for match in matchs:
        # Get the content of the match
        mountPoint, raidState, raidType, disksList, total, other, diskState, other2 = match

        # Get failed disk
        disks = disksList.split(" ")
        failedDisks = []
        for index, char in enumerate(diskState):
            if char == "_":
                failedDisks.append(disks[index])

        # Change the message according to the type
        if failedDisks:
            message += f"## *{mountPoint}* RAID status: KO\n"
            message += f"> **Failed disks**: {', '.join(failedDisks)}\n"
        else:
            message += f"## *{mountPoint}* RAID status: OK\n"
            message += f"All disks are operational !\n"

        # Add the informations
        message += f"### Informations :\n"
        message += f"- **RAID type**: {raidType}\n"
        message += f"- **RAID state**: {raidState}\n"
        message += f"- **Disks list**: {', '.join(disks)}\n"
        message += f"- **Total**: {total}\n"
        message += "\n"
    
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
    ntfy_url = os.getenv('NTFY_URL')
    ntfy_token = os.getenv('NTFY_TOKEN')

    # Read the content of the mdstat file
    mdstat_content = read_mdstat_file(mdstat_file)

    # ReGex pattern
    pattern = r"(\w+) : (\w+) (raid\d+) (.+)\n +(\d+) (.+) \[\d+\/\d+\] \[([U_]+)\]\n + \w+: \d+\/\d+ (.+)"

    # Search for the match in the mdstat file
    matches = get_match(mdstat_content, pattern)

    # Get status of the RAID
    raids_status = is_all_disks_ok(matches)

    # Generate the markdown message
    markdown = markdown_factory(matches)

    if raids_status:
        print("RAID status: OK")

        # NTFY notification variable
        headers = {
            "Markdown": "yes",
            "Title": "Check My Raid!",
            "Priority": "low",
            "Tags": "white_check_mark,cd"
        }
        data = markdown
        auth = ("", ntfy_token)

    else:
        print("RAID status: KO")
        # NTFY notification variable
        headers = {
            "Markdown": "yes",
            "Title": "Check My Raid!",
            "Priority": "high",
            "Tags": "warning,cd"
        }
        data = markdown
        auth = ("", ntfy_token)

    # Send the notification
    send_ntfy_notification(ntfy_url, headers, data, auth)

#######################################################################################
# Start the script 1 time on launch
main()

# Get the timezone and the schedule time
timezone = os.getenv('TZ', 'UTC')
trigerAt = os.getenv('TRIGER_SCHEDULE_AT')

# Get the current date and time on the timezone
tz = pytz.timezone(timezone)
now = datetime.datetime.now(tz)

print("Date and time is currently on the timezone", timezone, ":", now.strftime("%Y-%m-%d %H:%M:%S"))
print(f"Next raid check scheduled at {trigerAt} \n")

# Schedule the script to run at a specific time
schedule.every().day.at(trigerAt, timezone).do(main)

# Schedule loop
while True:
    schedule.run_pending()
    time.sleep(1)
