import asyncio

from crawlers.common import get_country
from crawlers.amazon_crawler import run_crawler_for_amazon
from crawlers.microsoft import run_crawler_for_microsoft
from crawlers.intel_crawler import run_crawler_for_intel
from crawlers.pg_crawler import run_crawler_for_pg

CRAWLERS = [
    run_crawler_for_amazon,
    run_crawler_for_microsoft,
    run_crawler_for_intel,
    run_crawler_for_pg
]


def check_new_job(receiverEmail=None):
    """One pass over every company. Emails only the jobs that were not in the database yet."""
    print(f"Checking for new jobs in {get_country()}...")
    for run_crawler in CRAWLERS:
        try:
            asyncio.run(run_crawler(receiverEmail))
        except Exception as error:
            print(f"{run_crawler.__name__} failed: {error}")


if __name__ == "__main__":
    # Entry point for the GitHub Actions cron. The receiver comes from JOB_RADAR_DEFAULT_RECEIVER.
    check_new_job()
