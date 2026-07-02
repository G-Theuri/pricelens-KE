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


async def visit_url(browser, semaphore, url):
    try:
        async with semaphore:
            tab = await browser.get(url, new_tab=True)
            try:
                await tab.wait(5)
                return await extract_data(tab, url)
            finally:
                await tab.close()
    except Exception as e:
        logger.info(f"Error getting response from {url} : {e}")
    

async def extract_data(tab, url):
    try:
        logger.info(f"Extracting data from: {url}")
        listings_data = await tab.evaluate("""
            JSON.stringify(
                Array.from(document.querySelectorAll('article a.core:not([data-spon="true"])'))
                .filter(el => el.querySelector("div.info h3.name") !== null)
                .map(el => {
                    const priceEl = el.querySelector("div.info div.prc");
                    const name = el.querySelector("div.info h3.name");
                    return {
                        platform_sku: el.getAttribute("data-gtm-id"),
                        title_raw: name.innerText,
                        url: el.href,
                        current_price: priceEl ? parseFloat(priceEl.innerText.replace(/[^0-9.]/g, "")) : null,
                        platform: 'jumia',
                    };
                })
                )
            """)

        return json.loads(listings_data)
    except Exception as e:
        logger.error(f"Error extracting data: {e}")

async def upsert(listings_data):
    try:
        response = supabase.table('listings').upsert(listings_data, on_conflict="platform,url").execute()
        return response
    except Exception as e:
        logger.error(f"Error upserting to supabase: {e}")
        return None
    
async def main():
    MAX_CONCURENT = 10
    listings = []
    
    browser = await uc.start()
    urls  = [f'https://www.jumia.co.ke/phones-tablets/?page={p}#catalog-listing' for p in range(1, 7)]
    
    logger.info("-"*110)
    logger.info(f"Scraping {len(urls)} pages")
    semaphore = asyncio.Semaphore(MAX_CONCURENT)
    logger.info(f"Limiting to {MAX_CONCURENT} active tabs.")

    tasks = [visit_url(browser, semaphore, url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Scraping page failed {result}")
        else:
            print(result)
            listings.extend(result)

    listings = list({(l["platform"], l["url"]): l for l in listings}.values())
    if listings:
        response = await upsert(listings)
        logger.info(f"Upserted {len(response.data)} rows")
        logger.info("Finished successfully!")
    logger.info("-"*110)



if __name__ == "__main__":
    uc.loop().run_until_complete(main())


