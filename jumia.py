import nodriver as uc
from rich import print
from loguru import logger
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()
import os
import asyncio
import json


logger.add("jumia_scraper.log", enqueue="True")
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

async def extract_data(tab, url):
    logger.info(f"Extracting data from: {url}")
    listings_data = await tab.evaluate("""
        Array.from(document.querySelectorAll("article a.core")).map(el => {
            const priceEl = el.querySelector("div.info div.prc");
            const imgsrc = el.querySelector("div.img-c img");
            return {
                SKU: el.getAttribute("data-gtm-id"),
                url: el.href,
                img: imgsrc ? imgsrc.src : null,
                Price: priceEl ? priceEl.innerText : null,
            };
        });
        """)

    for info in listings_data:
        print(json.dumps(info, indent=4))




async def visit_url(browser, semaphore, url):
    async with semaphore:
        tab = await browser.get(url, new_tab=True)
        await tab.wait(5)
        await extract_data(tab, url)
        await tab.close()


async def main():
    browser = await uc.start()
    
    semaphore = asyncio.Semaphore(10)
    urls  = [f'https://www.jumia.co.ke/phones-tablets/?page={p}#catalog-listing' for p in range(1, 2)]
    tasks = [visit_url(browser, semaphore, url) for url in urls]
    results = await asyncio.gather(*tasks)


if __name__ == "__main__":
    uc.loop().run_until_complete(main())


