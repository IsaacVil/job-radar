import asyncio

import requests

from crawlers.common import get_country, get_searches, matches_title_keywords, publish_new_jobs, report_dropped

COMPANY = "Microsoft"
SEARCH_API = "https://apply.careers.microsoft.com/api/pcsx/search"
JOB_PAGE = "https://jobs.careers.microsoft.com/global/en/job/{job_id}"
PAGE_SIZE = 20
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def search_jobs(search, country, start):
    params = {
        "domain": "microsoft.com",
        "query": search.get("query", ""),
        "location": search.get("location", country),
        "start": start,
        "num": PAGE_SIZE
    }
    response = requests.get(SEARCH_API, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json().get("data") or {}


def fetch_jobs(search, country):
    # Microsoft calls its categories "departments" and returns one per posting
    categories = [category.lower() for category in search.get("categories", [])]
    keywords = search.get("title_keywords", [])

    jobs = []
    dropped = {}
    start = 0
    total = None
    max_jobs = search.get("max_jobs", 100)

    while total is None or (start < total and start < max_jobs):
        data = search_jobs(search, country, start)
        total = data.get("count", 0)
        positions = data.get("positions", [])
        if not positions:
            break

        for position in positions:
            # A posting can be open in several countries at once, keep it only if one of them is ours
            locations = position.get("locations") or []
            if not any(country.lower() in location.lower() for location in locations):
                continue

            department = position.get("department") or "?"
            if categories and department.lower() not in categories:
                dropped[department] = dropped.get(department, 0) + 1
                continue
            if not matches_title_keywords(position.get("name"), keywords):
                dropped[department] = dropped.get(department, 0) + 1
                continue

            job_id = position.get("displayJobId") or position.get("id")
            jobs.append({
                "company": COMPANY,
                "title": position.get("name"),
                "number": str(job_id),
                "link": JOB_PAGE.format(job_id=job_id),
                "location": ", ".join(locations)
            })

        start += PAGE_SIZE

    report_dropped(COMPANY, dropped)
    return jobs


async def run_crawler_for_microsoft(receiverEmail=None):
    country = get_country()
    searches = get_searches(COMPANY)
    results = await asyncio.gather(
        *(asyncio.to_thread(fetch_jobs, search, country) for search in searches),
        return_exceptions=True
    )

    all_jobs = []
    for search, result in zip(searches, results):
        if isinstance(result, Exception):
            print(f"{COMPANY}: search {search} failed: {result}")
            continue
        all_jobs.extend(result)
        publish_new_jobs(COMPANY, result, receiverEmail)

    return all_jobs


if __name__ == "__main__":
    asyncio.run(run_crawler_for_microsoft())
