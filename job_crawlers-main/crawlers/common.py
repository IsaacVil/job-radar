import json
import os

from database.job_store import add_jobs_if_not_exists
from email_config.email_setup import send_email
from notifications.ntfy_setup import send_push

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "urls", "urls.json"
)


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)


def get_country():
    """Country every crawler filters on. Configured once in urls/urls.json."""
    return load_config().get("country", "Costa Rica")


def get_searches(company):
    return load_config().get("companies", {}).get(company, [])


def publish_new_jobs(company, jobs, receiverEmail=None):
    """Remember the jobs that were not seen before and notify only those."""
    if not jobs:
        return []

    new_jobs = add_jobs_if_not_exists(jobs)
    print(f"{company}: {len(jobs)} job(s) in {get_country()}, {len(new_jobs)} new")

    if new_jobs:
        send_push(new_jobs)                    # ntfy, no credentials needed
        send_email(new_jobs, receiverEmail)    # only if the SMTP variables are set

    return new_jobs
