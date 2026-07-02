from curl_cffi import requests as cureq
from rich import print
import json
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()
import os
from loguru import logger

logger.add("kilimall_scraper.log", enqueue = "True")
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def visit_url(url):
    try:
        response =  cureq.get(url,impersonate='chrome')
        return extract_data(response)
    
    except Exception as e:
        logger.error(f"Failed to get response: {e}")

def extract_data(response):
    try:
        listings = response.json().get("data").get("result")
        data = []
        for listing in listings:
            info = {

                "platform_sku": listing.get("defaultSkuId"),
                "title_raw": listing.get("shortTitle") or listing.get("title"),
                "url": "https://www.kilimall.co.ke/listing/" + str(listing.get("listingId")),
                "current_price": listing.get("price"),
        }
            info['platform'] = 'kilimall'
            data.append(info)

        return data
    except Exception as e:
        logger.error(f"Failed to extract data: {e}")

def upsert(data):
    try:
        logger.info("Upserting data into supabase ...")
        upsert_response = supabase.table("listings").upsert(data, on_conflict="platform, url").execute()
        return upsert_response
    
    except Exception as e:
        logger.error(f"Error upserting data into supabase: {e}")

def main():
    logger.info("-"*110)
    urls = [f"https://mall-api.kilimall.com/search?skip={p-500}&size={p}&frontCategoryId=872&useSuggestion=true&limit=36" for p in range(500, 2000, 500)]
    
    all_data = []
    logger.info("Extracting listings data from API ...")
    for url in urls:
        all_data.extend(visit_url(url))

    all_data = list({(l["platform"], l["url"]): l for l in all_data}.values())
    upsert_response = upsert(all_data)
    logger.info(f"Upserted {len(upsert_response.data)} rows")
    logger.info("Finished successfully!")

    logger.info("-"*110)


if __name__ == "__main__":
    main()