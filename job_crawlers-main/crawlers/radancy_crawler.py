import asyncio
import html
import re

import requests

from crawlers.common import get_country, get_searches, matches_title_keywords, publish_new_jobs

HEADERS = {
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest",  # Without it Radancy answers with the full page instead of JSON
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
CATEGORY_FACET = "1"
COUNTRY_FACET = "2"
FACET_INPUT = re.compile(r'<input[^>]*data-facet-type="(\d+)"[^>]*>')
JOB_LINK = re.compile(
    r'<a href="(?P<path>/[^"]+)"[^>]*data-job-id="(?P<id>\d+)"[^>]*>\s*<h2>(?P<title>.*?)</h2>'
    r'(?:.*?<span class="job-location">(?P<location>.*?)</span>)?',
    re.S
)


def search_jobs(search, facets, page):
    """Radancy (TalentBrew) sites answer with the rendered filters and results as HTML inside a JSON envelope."""
    params = [
        ("ActiveFacetID", "0"),
        ("CurrentPage", page),
        ("RecordsPerPage", 100),
        ("Keywords", search.get("search_text", "")),
        ("SearchResultsModuleName", "Search Results"),
        ("SearchFiltersModuleName", "Search Filters"),
        ("SearchType", "5")
    ]
    for index, facet in enumerate(facets):
        params += [
            (f"FacetFilters[{index}].ID", facet["id"]),
            (f"FacetFilters[{index}].FacetType", facet["type"]),
            (f"FacetFilters[{index}].Count", "0"),
            (f"FacetFilters[{index}].Display", facet["display"]),
            (f"FacetFilters[{index}].IsApplied", "true")
        ]
    response = requests.get(
        f"https://{search['host']}/{search.get('language', 'en')}/search-jobs/results",
        params=params, headers=HEADERS, timeout=30
    )
    response.raise_for_status()
    return response.json()


def find_facets(filters_html):
    """Facet ids are looked up by their label, like on Workday, instead of being hardcoded."""
    facets = []
    for match in FACET_INPUT.finditer(filters_html or ""):
        attributes = dict(re.findall(r'data-([a-z-]+)="([^"]*)"', match.group(0)))
        facets.append({
            "type": match.group(1),
            "id": attributes.get("id"),
            "display": html.unescape(attributes.get("display", ""))
        })
    return facets


def fetch_jobs(company, search, country):
    facets = find_facets(search_jobs(search, [], 1).get("filters"))
    country_facets = [f for f in facets if f["type"] == COUNTRY_FACET and f["display"].lower() == country.lower()]
    if not country_facets:
        print(f"{company}: no open jobs in {country}")
        return []

    categories = [category.lower() for category in search.get("categories", [])]
    applied = country_facets
    if categories:
        category_facets = [f for f in facets if f["type"] == CATEGORY_FACET and f["display"].lower() in categories]
        if not category_facets:
            print(f"{company}: no category matched {search['categories']}")
            return []
        applied = applied + category_facets

    keywords = search.get("title_keywords", [])
    jobs = []
    dropped = 0
    page = 1
    max_jobs = search.get("max_jobs", 100)

    while len(jobs) + dropped < max_jobs:
        results = search_jobs(search, applied, page).get("results") or ""
        matches = list(JOB_LINK.finditer(results))
        if not matches:
            break

        for match in matches:
            title = html.unescape(re.sub(r"<[^>]+>", "", match.group("title"))).strip()
            if not matches_title_keywords(title, keywords):
                dropped += 1
                continue
            jobs.append({
                "company": company,
                "title": title,
                "number": match.group("id"),
                "link": f"https://{search['host']}{match.group('path')}",
                "location": html.unescape(match.group("location") or country).strip()
            })

        if len(matches) < 100:
            break
        page += 1

    if dropped:
        print(f"{company}: ignored {dropped} job(s) whose title matched no keyword")

    return jobs


async def run_crawler_for_radancy(company, receiverEmail=None):
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
