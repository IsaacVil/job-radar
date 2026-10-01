import asyncio

import requests

from crawlers.common import get_country, get_searches, matches_title_keywords, publish_new_jobs, report_dropped

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def fetch_jobs(company, search, country):
    # Greenhouse returns the whole board in one response, filtering happens here.
    # Departments are only included with content=true
    response = requests.get(
        f"https://boards-api.greenhouse.io/v1/boards/{search['board']}/jobs",
        params={"content": "true"}, headers=HEADERS, timeout=30
    )
    response.raise_for_status()

    # Offices are often named after the city only ("San José"), so they are listed next to the country
    locations = [location.lower() for location in search.get("locations", [country])]
    categories = [category.lower() for category in search.get("categories", [])]
    keywords = search.get("title_keywords", [])

    jobs = []
    dropped = {}
    for job in response.json().get("jobs", []):
        places = [(job.get("location") or {}).get("name") or ""]
        places += [office.get("name") or "" for office in job.get("offices", [])]
        if not any(location in place.lower() for place in places for location in locations):
            continue

        departments = [(department.get("name") or "").strip() for department in job.get("departments", [])]
        department = departments[0] if departments else "?"
        if categories and not any(name.lower() in categories for name in departments):
            dropped[department] = dropped.get(department, 0) + 1
            continue
        if not matches_title_keywords(job.get("title"), keywords):
            dropped[department] = dropped.get(department, 0) + 1
            continue

        jobs.append({
            "company": company,
            "title": (job.get("title") or "").strip(),
            "number": str(job["id"]),
            "link": job.get("absolute_url"),
            "location": places[0]
        })

    report_dropped(company, dropped)
    return jobs


async def run_crawler_for_greenhouse(company, receiverEmail=None):
    country = get_country()
    searches = get_searches(company)
    results = await asyncio.gather(
        *(asyncio.to_thread(fetch_jobs, company, search, country) for search in searches),
        return_exceptions=True
    )

    all_jobs = []
    for search, result in zip(searches, results):
        if isinstance(result, Exception):
            print(f"{company}: search {search} failed: {result}")
            continue
        all_jobs.extend(result)
        publish_new_jobs(company, result, receiverEmail)

    return all_jobs
