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
        JSON.stringify(
            Array.from(document.querySelectorAll('article a.core:not([data-spon="true"])'))
            .filter(el => el.querySelector("div.info h3.name") !== null)
            .map(el => {
                const priceEl = el.querySelector("div.info div.prc");
                const imgsrc = el.querySelector("div.img-c img");
                const name = el.querySelector("div.info h3.name");
                return {
                    platform_sku: el.getAttribute("data-gtm-id"),
                    title_raw: name.innerText,
                    url: el.href,
                    img: imgsrc ? imgsrc.src : null,
                    current_price: priceEl ? parseFloat(priceEl.innerText.replace(/[^0-9.]/g, "")) : null,
                    platform: 'jumia',
                };
            })
            )
        """)
    
    if listings_data:
        print(json.loads(listings_data))
        await upsert(json.loads(listings_data))

async def upsert(listings_data):
    supabase.table('listings').upsert(listings_data, on_conflict="platform,url").execute()
    


async def visit_url(browser, semaphore, url):
    async with semaphore:
        tab = await browser.get(url, new_tab=True)
        await tab.wait(5)
        await extract_data(tab, url)
        await tab.close()


async def main():
    browser = await uc.start()
    
    semaphore = asyncio.Semaphore(10)
    urls  = [f'https://www.jumia.co.ke/phones-tablets/?page={p}#catalog-listing' for p in range(1, 3)]
    tasks = [visit_url(browser, semaphore, url) for url in urls]
    results = await asyncio.gather(*tasks)

    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            logger.error(f"FAILED {url}: {result}")
        else:
            logger.info(f"OK {url}: {result} listings upserted")


if __name__ == "__main__":
    uc.loop().run_until_complete(main())


