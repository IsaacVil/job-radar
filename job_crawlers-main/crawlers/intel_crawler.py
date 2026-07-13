import asyncio

from crawlers.workday_crawler import run_crawler_for_workday

COMPANY = "Intel"


async def run_crawler_for_intel(receiverEmail=None):
    return await run_crawler_for_workday(COMPANY, receiverEmail)


if __name__ == "__main__":
    asyncio.run(run_crawler_for_intel())
