import asyncio
import re

import requests

from crawlers.common import get_country, get_searches, matches_title_keywords, publish_new_jobs, report_dropped

COMPANY = "IBM"
SEARCH_API = "https://www-api.ibm.com/search/api/v2"
PAGE_SIZE = 50
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
# IBM's search index names its fields generically
COUNTRY_FIELD = "field_keyword_05"
CATEGORY_FIELD = "field_keyword_08"
CITY_FIELD = "field_keyword_19"


def search_jobs(country, offset):
    payload = {
        "appId": "careers",
        "scopes": ["careers2"],
        "query": {"bool": {"must": []}},
        "post_filter": {"term": {COUNTRY_FIELD: country}},
        "size": PAGE_SIZE,
        "from": offset,
        "_source": ["url", "title", COUNTRY_FIELD, CATEGORY_FIELD, CITY_FIELD]
    }
    response = requests.post(SEARCH_API, json=payload, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json().get("hits") or {}


def fetch_jobs(search, country):
    categories = [category.lower() for category in search.get("categories", [])]
    keywords = search.get("title_keywords", [])

    jobs = []
    dropped = {}
    offset = 0
    total = None
    max_jobs = search.get("max_jobs", 100)

    while total is None or (offset < total and offset < max_jobs):
        hits = search_jobs(country, offset)
        total = (hits.get("total") or {}).get("value", 0)
        page = hits.get("hits", [])
        if not page:
            break

        for hit in page:
            job = hit.get("_source", {})
            category = job.get(CATEGORY_FIELD) or "?"
            if categories and category.lower() not in categories:
                dropped[category] = dropped.get(category, 0) + 1
                continue
            if not matches_title_keywords(job.get("title"), keywords):
                dropped[category] = dropped.get(category, 0) + 1
                continue

            link = job.get("url", "")
            job_id = re.search(r"jobId=(\d+)", link)
            jobs.append({
                "company": COMPANY,
                "title": job.get("title"),
                "number": job_id.group(1) if job_id else link,
                "link": link,
                "location": job.get(CITY_FIELD) or job.get(COUNTRY_FIELD)
            })

        offset += PAGE_SIZE

    report_dropped(COMPANY, dropped)
    return jobs


async def run_crawler_for_ibm(receiverEmail=None):
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
    asyncio.run(run_crawler_for_ibm())
