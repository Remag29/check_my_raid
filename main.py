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


def read_mdstat_file(file_path) -> str:
    """Read the content of the mdstat file."""
    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
        exit(1)


def send_ntfy_notification(url, headers, data, auth):
    """Send an HTTP POST request to trigger a notification on NTFY."""
    response = requests.post(url, headers=headers,
                             data=data.encode('utf-8'), auth=auth)
    if response.status_code == 200:
        print("Notificationn sent successfully.")
    else:
        print("Échec de l'envoi de la notification.")
        print(f"Failed to sent request. Status code: {response.status_code}")

def main():

    # Variables
    mdstat_file = "/app/data/mdstat"
    ntfy_url = os.getenv('NTFY_URL')
    ntfy_token = os.getenv('NTFY_TOKEN')

    # Read the content of the mdstat file
    mdstat_content = read_mdstat_file(mdstat_file)

    # ReGex pattern
    pattern = r" +\d+ \w+ \w+ [0-9.]+ \[\d\/\d\] \[([U_]+)\]"

    # Search for the match in the mdstat file
    matches = re.findall(pattern, mdstat_content)
    if matches:
        # Print the result of the regex
        content = matches[0]
        print(f"Résultat de la regex : {content}")

        # Check if the content is "UU"
        if content == "UU":
            print("RAID status: OK")

            # NTFY notification
            headers = {
                "Title": "RAID OK",
                "Priority": "low",
                "Tags": "white_check_mark,cd"
            }
            data = "CheckMyRaid doesn't detect any anomaly on the RAID"
            auth = ("", ntfy_token)

            send_ntfy_notification(ntfy_url, headers, data, auth)

        else:
            print("RAID status: KO")

            # NTFY notification
            headers = {
                "Title": "Anomalie RAID",
                "Priority": "max",
                "Tags": "warning,cd"
            }
            data = "An anomaly has been detected on the RAID. Please check the RAID status as soon as possible."
            auth = ("", ntfy_token)

            send_ntfy_notification(ntfy_url, headers, data, auth)
    else:
        print("No match found. Verify the content of the mdstat file.")
    print("")

# Start the script 1 time on launch
main()

# Schedule the script to run at a specific time
timezone = os.getenv('TZ', 'UTC')
trigerAt = os.getenv('TRIGER_SCHEDULE_AT')

tz = pytz.timezone(timezone)
now = datetime.datetime.now(tz)

print("Date and time is currently on the timezone", timezone, ":", now.strftime("%Y-%m-%d %H:%M:%S"))
print(f"Next raid check scheduled at {trigerAt} \n")
schedule.every().day.at(trigerAt, timezone).do(main)

while True:
    schedule.run_pending()
    time.sleep(1)
