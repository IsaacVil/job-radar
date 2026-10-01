import asyncio

from crawlers.common import get_country
from crawlers.amazon_crawler import run_crawler_for_amazon
from crawlers.microsoft import run_crawler_for_microsoft
from crawlers.intel_crawler import run_crawler_for_intel
from crawlers.pg_crawler import run_crawler_for_pg
from crawlers.ibm_crawler import run_crawler_for_ibm
from crawlers.workday_crawler import run_crawler_for_workday
from crawlers.eightfold_crawler import run_crawler_for_eightfold
from crawlers.greenhouse_crawler import run_crawler_for_greenhouse
from crawlers.radancy_crawler import run_crawler_for_radancy

CRAWLERS = [
    run_crawler_for_amazon,
    run_crawler_for_microsoft,
    run_crawler_for_intel,
    run_crawler_for_pg,
    run_crawler_for_ibm
]

# Companies on a shared job platform need no crawler of their own, only their searches in urls.json
PLATFORM_CRAWLERS = {
    "Konrad": run_crawler_for_greenhouse,
    "Cisco": run_crawler_for_workday,
    "HP": run_crawler_for_workday,
    "Moody's": run_crawler_for_radancy,
    "HPE": run_crawler_for_workday,
    "Boston Scientific": run_crawler_for_eightfold,
    "Stryker": run_crawler_for_workday,
    "Equifax": run_crawler_for_workday
}


def check_new_job(receiverEmail=None):
    """One pass over every company. Notifies only the jobs that were not seen yet."""
    print(f"Checking for new jobs in {get_country()}...")
    for run_crawler in CRAWLERS:
        try:
            asyncio.run(run_crawler(receiverEmail))
        except Exception as error:
            print(f"{run_crawler.__name__} failed: {error}")

    for company, run_crawler in PLATFORM_CRAWLERS.items():
        try:
            asyncio.run(run_crawler(company, receiverEmail))
        except Exception as error:
            print(f"{company} crawler failed: {error}")


if __name__ == "__main__":
    # Entry point for the GitHub Actions cron. The receiver comes from JOB_RADAR_DEFAULT_RECEIVER.
    check_new_job()
