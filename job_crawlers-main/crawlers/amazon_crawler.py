import asyncio

import requests

from crawlers.common import get_country, get_searches, publish_new_jobs

COMPANY = "Amazon"
SEARCH_URL = "https://www.amazon.jobs/en/search.json"
SITE_URL = "https://www.amazon.jobs"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def fetch_jobs(search):
    country_code = search.get("country_code", "CRI")
    params = {
        "normalized_country_code[]": country_code,
        "base_query": search.get("base_query", ""),
        "result_limit": search.get("result_limit", 100),
        "offset": 0,
        "sort": "recent"
    }
    response = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()

    jobs = []
    for job in response.json().get("jobs", []):
        if job.get("country_code") != country_code:
            continue
        jobs.append({
            "company": COMPANY,
            "title": job.get("title"),
            "number": job.get("id_icims"),
            "link": SITE_URL + job.get("job_path", ""),
            "location": job.get("normalized_location") or job.get("city")
        })
    return jobs


async def run_crawler_for_amazon(receiverEmail=None):
    searches = get_searches(COMPANY)
    results = await asyncio.gather(
        *(asyncio.to_thread(fetch_jobs, search) for search in searches),
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
    print(get_country())
    asyncio.run(run_crawler_for_amazon())
