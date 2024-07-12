# Check My RAID

A simple docker container that checks the status of a RAID array made with [mdadm](https://fr.wikipedia.org/wiki/Mdadm)
and sends a notification with [NTFY](https://ntfy.sh/) of the status.

## Usage

Clone the repository and build the image with the following command:

```bash
git clone https://github.com/Remag29/check_my_raid.git
```

```bash
docker compose build
```

```bash
docker compose up -d
```

## Docker compose

```yaml
services:
  checkmyraid:
    image: checkmyraid
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - /proc/mdstat:/app/data/mdstat:ro
    env_file:
      - .env
    restart: unless-stopped
```

Don't forget to create a .env file with the following content:

```env
TZ=Europe/paris
TRIGER_SCHEDULE_AT="12:00"
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/REDACTED/REDACTED
```

## How it works

The container is simply a python script that reads the /proc/mdstat to check the status of the RAID array.

The script is made to check the status of multiple RAID arrays. For example, if you have two RAID arrays md0 and md1,
Check My RAID will check the status of both.

A single notification is sent for all the RAID arrays. The notification contains the detailed status of each RAID array.

The script is searching raid arrays with the following regex:

```regex
(\w+) : (\w+) (raid\d+) (.+)\n +(\d+) (.+) \[\d+\/\d+\] \[([U_]+)\]\n + \w+: \d+\/\d+ (.+)
```

This regex is made to match with mdstat file format and allows to extract some information like the name of the RAID
array, the type of RAID, the status, the number of disks, the status of each disk, and the name of each disk.

The script is checking the status of the RAID array by looking for the beacons `[UU]`. If the status is `[UU]`, the RAID
array is considered healthy, but if some "U" are replaced by "_", the RAID array is considered degraded.

The notification is sent with Discord Webhook. The URL of the webhook is set with the variable `DISCORD_WEBHOOK_URL`.

The script is scheduled to run every day at a specific time set with the variable `TRIGER_SCHEDULE_AT`.
