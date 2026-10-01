import asyncio

from crawlers.eightfold_crawler import run_crawler_for_eightfold

COMPANY = "Microsoft"


async def run_crawler_for_microsoft(receiverEmail=None):
    return await run_crawler_for_eightfold(COMPANY, receiverEmail)


if __name__ == "__main__":
    asyncio.run(run_crawler_for_microsoft())
