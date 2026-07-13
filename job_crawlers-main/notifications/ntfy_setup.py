import os

import requests

# ntfy needs no account and no token: the topic name is the whole address.
# Pick an unguessable one and subscribe to it from the ntfy app.
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")
MAX_JOBS_IN_MESSAGE = 8  # ntfy caps a message at 4KB, so long batches are summarized


def send_push(jobs):
    if not NTFY_TOPIC:
        print("No NTFY_TOPIC set, skipping the push notification.")
        return

    company = jobs[0]["company"]
    lines = [f"{job['title']} - {job.get('location', '')}\n{job['link']}" for job in jobs[:MAX_JOBS_IN_MESSAGE]]
    remaining = len(jobs) - MAX_JOBS_IN_MESSAGE
    if remaining > 0:
        lines.append(f"...and {remaining} more")

    try:
        response = requests.post(
            f"{NTFY_SERVER}/{NTFY_TOPIC}",
            data="\n\n".join(lines).encode("utf-8"),
            headers={
                "Title": f"{len(jobs)} new {company} job(s)",
                "Tags": "briefcase",
                "Click": jobs[0]["link"]
            },
            timeout=30
        )
        response.raise_for_status()
        print(f"Push notification sent for {len(jobs)} {company} job(s).")
    except requests.RequestException as error:
        print(f"Could not send the push notification: {error}")
