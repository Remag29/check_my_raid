# Check My RAID

A simple docker container that checks the status of a RAID array made with [mdadm](https://fr.wikipedia.org/wiki/Mdadm)
and sends a notification with Discord of the status.

## Usage

Clone the repository and build the image with the following command:

```bash
git clone https://github.com/Remag29/check_my_raid.git
```

Make a copy of the `example.env` file:

```bash
cp example.env .env
```

Edit the `.env` file and set the `DISCORD_WEBHOOK_URL` variable with the URL of your Discord webhook.

Then build the image with the following command:

```bash
docker compose up -d
```

## Docker compose

```yaml
---
services:
    checkmyraid:
        image: remag29/check_my_raid:latest
        volumes:
            - /proc/mdstat:/app/data/mdstat:ro
        environment:
            - TZ='Europe/Paris'
            - CHECK_ON_STARTUP=False
            - TRIGER_SCHEDULE_AT='12:00'
            - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
        restart: unless-stopped
```

Remember to create a .env file with the following content:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/REDACTED/REDACTED
```
## Variables

| Variable              | Description                                                      | Default |
|-----------------------|------------------------------------------------------------------|---------|
| `TZ`                  | Timezone                                                         | `UTC`   |
| `CHECK_ON_STARTUP`    | Check the status of the RAID array when the container is started | `None`  |
| `TRIGER_SCHEDULE_AT`  | Time to check the status of the RAID array (format: HH:MM)       | `12:00` |
| `DISCORD_WEBHOOK_URL` | URL of the Discord webhook                                       | `None`  |
## How it works

The container is simply a python script that reads the file `/proc/mdstat` to check the status of the RAID array.

The script is made to check the status of multiple RAID arrays. For example, if you have two RAID arrays md0 and md1,
check_my_raid will check the status of both.

A single notification is sent for all the RAID arrays. The notification contains the detailed status of each RAID array.

The script is checking the status of the RAID array by looking for the beacons `[UU]`.
If the status is `[UU]`, the RAID array is considered healthy,
but if some "U" are replaced by "_", the RAID array is considered degraded.

The notification is sent with Discord Webhook. The URL of the webhook is set with the variable `DISCORD_WEBHOOK_URL`.

The script is scheduled to run every day at a specific time set with the variable `TRIGER_SCHEDULE_AT`.

You can also set the variable `CHECK_ON_STARTUP` to `True` to check the status of the RAID array when the container is
started.
