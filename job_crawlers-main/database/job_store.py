import json
import os

# Which jobs were already notified. It lives in the repo so the GitHub Actions cron can keep
# state between runs without a database (and therefore without any credential).
STORE_PATH = os.environ.get(
    "JOB_RADAR_STORE",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "seen_jobs.json")
)


def load_seen_jobs():
    if not os.path.exists(STORE_PATH):
        return {}
    with open(STORE_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_seen_jobs(seen_jobs):
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    for job_numbers in seen_jobs.values():
        job_numbers.sort()  # Keeps the diff of every cron commit readable
    with open(STORE_PATH, 'w', encoding='utf-8') as file:
        json.dump(seen_jobs, file, indent=2, ensure_ascii=False, sort_keys=True)


def add_jobs_if_not_exists(jobs):
    """Return the jobs that were never seen before, and remember them."""
    if not jobs:
        return []

    seen_jobs = load_seen_jobs()
    new_jobs = []

    for job in jobs:
        company_jobs = seen_jobs.setdefault(job["company"], [])
        number = str(job["number"])
        if number in company_jobs:
            continue
        company_jobs.append(number)
        new_jobs.append(job)

    if new_jobs:
        save_seen_jobs(seen_jobs)

    return new_jobs
