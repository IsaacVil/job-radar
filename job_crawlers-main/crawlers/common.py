import json
import os
import re

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


def matches_title_keywords(title, keywords):
    """Whole word match, so "IT" does not match "Digital" and "data" does not match "database"."""
    if not keywords:
        return True
    return any(re.search(rf"\b{re.escape(keyword)}\b", title or "", re.IGNORECASE) for keyword in keywords)


def report_dropped(company, dropped_categories):
    """Name the categories that were filtered out, so it is obvious what to add to urls.json to widen the search."""
    if dropped_categories:
        summary = ", ".join(f"{category} ({count})" for category, count in sorted(dropped_categories.items()))
        print(f"{company}: ignored jobs in {summary}")


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
