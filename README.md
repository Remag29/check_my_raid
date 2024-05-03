# Check My RAID

A simple docker container that checks the status of a RAID array made with [mdadm](https://fr.wikipedia.org/wiki/Mdadm) and sends a notification with [NTFY](https://ntfy.sh/) of the status.

## Usage

Clone the repository and build the image with the following command:

```bash
git clone https://github.com/Remag29/check_my_raid.git
```

```bash
docker compose up -d --build
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
NTFY_URL=changeme
NTFY_TOKEN=changeme
```

## How it works

The container is simply a python script that reads the /proc/mdstat to check the status of the RAID array.

Currently, the script is made to check the status of a single RAID array. Work in progress !

The script search the pattern "[UU]", that symbolizes the RAID health. If this pattern change for something like "[_U]", the script sends a notification with NTFY.

The notification sent with NTFY is a simple message with the status of the RAID array. You can specify the URL and the token of your NTFY account with the variables `NTFY_URL` and `NTFY_TOKEN`.

The script is scheduled to run every day at a specific time set with the variable `TRIGER_SCHEDULE_AT`.
