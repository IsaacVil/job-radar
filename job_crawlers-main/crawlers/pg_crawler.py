import asyncio

from crawlers.workday_crawler import run_crawler_for_workday

COMPANY = "P&G"


async def run_crawler_for_pg(receiverEmail=None):
    return await run_crawler_for_workday(COMPANY, receiverEmail)


if __name__ == "__main__":
    asyncio.run(run_crawler_for_pg())
