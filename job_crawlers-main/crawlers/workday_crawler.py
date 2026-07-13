import asyncio

import requests

from crawlers.common import get_country, get_searches, matches_title_keywords, publish_new_jobs

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
PAGE_SIZE = 20  # Workday caps every page of its search API at 20 postings


def api_url(search):
    return f"https://{search['tenant']}.myworkdayjobs.com/wday/cxs/{search['site']}/jobs"


def job_url(search, external_path):
    site_name = search['site'].split('/')[-1]
    return f"https://{search['tenant']}.myworkdayjobs.com/en-US/{site_name}{external_path}"


def search_jobs(search, applied_facets, search_text, offset):
    payload = {
        "appliedFacets": applied_facets,
        "limit": PAGE_SIZE,
        "offset": offset,
        "searchText": search_text
    }
    response = requests.post(api_url(search), json=payload, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def matches_country(descriptor, country):
    # Workday labels locations as "Costa Rica" or "Costa Rica, San Jose" depending on the tenant
    parts = (descriptor or "").split(",")
    return any(part.strip().lower() == country.lower() for part in parts)


def matches_category(descriptor, categories):
    return (descriptor or "").strip().lower() in [category.lower() for category in categories]


def find_facets(node, matches, parameter=None, found=None):
    """Look facet ids up by their label: they are tenant specific and change over time."""
    if found is None:
        found = {}

    if isinstance(node, dict):
        parameter = node.get("facetParameter", parameter)
        if node.get("id") and matches(node.get("descriptor")):
            found.setdefault(parameter, []).append(node["id"])
        for value in node.values():
            find_facets(value, matches, parameter, found)
    elif isinstance(node, list):
        for value in node:
            find_facets(value, matches, parameter, found)

    return found


def fetch_jobs(company, search, country):
    facets = search_jobs(search, {}, "", 0).get("facets", [])
    categories = search.get("categories", [])
    keywords = search.get("title_keywords", [])

    applied_facets = find_facets(facets, lambda descriptor: matches_country(descriptor, country))
    search_text = search.get("search_text", "")

    if not applied_facets:
        # No location facet for the country: fall back to a text search and drop anything that is not there
        print(f"{company}: no Workday location facet for {country}, falling back to a text search")
        search_text = f"{search_text} {country}".strip()

    if categories:
        # Intel groups its jobs in job families; tenants without that facet fall back to title_keywords
        category_facets = find_facets(facets, lambda descriptor: matches_category(descriptor, categories))
        if category_facets:
            applied_facets.update(category_facets)
        else:
            print(f"{company}: no Workday category facet matched {categories}")

    jobs = []
    dropped = 0
    offset = 0
    total = None
    max_jobs = search.get("max_jobs", 100)

    while total is None or (offset < total and offset < max_jobs):
        page = search_jobs(search, applied_facets, search_text, offset)
        total = page.get("total", 0)
        postings = page.get("jobPostings", [])
        if not postings:
            break

        for posting in postings:
            location = posting.get("locationsText", "")
            external_path = posting.get("externalPath", "")
            title = posting.get("title")

            if not applied_facets and country.lower() not in f"{location} {external_path}".replace("-", " ").lower():
                continue
            if not matches_title_keywords(title, keywords):
                dropped += 1
                continue

            bullet_fields = posting.get("bulletFields") or []
            jobs.append({
                "company": company,
                "title": title,
                "number": bullet_fields[0] if bullet_fields else external_path,
                "link": job_url(search, external_path),
                "location": location
            })

        offset += PAGE_SIZE

    if dropped:
        print(f"{company}: ignored {dropped} job(s) whose title matched no keyword")

    return jobs


async def run_crawler_for_workday(company, receiverEmail=None):
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
