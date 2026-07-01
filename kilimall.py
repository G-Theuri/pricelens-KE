from curl_cffi import requests as cureq
from rich import print
import json
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()
import os


supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def visit_url():
    response =  cureq.get("https://mall-api.kilimall.com/search?skip=0&size=50&frontCategoryId=872&useSuggestion=true&limit=36",
                        impersonate='chrome')
    return response
def extract_data(response):
    listings = response.json().get("data").get("result")
    data = []
    for listing in listings:
        info = {

            "platform_sku": listing.get("defaultSkuId"),
            "title_raw": listing.get("shortTitle") or listing.get("title"),
            "url": "https://www.kilimall.co.ke/listing/" + str(listing.get("listingId")),
            "img": listing.get("image"),
            "current_price": listing.get("price"),
    }
        info['platform'] = 'kilimall'
        data.append(info)

    return data
def upsert(data):
    for info in data:
        supabase.table("listings").upsert(info, on_conflict="platform, url").execute()

def main():
    response = visit_url()
    data = extract_data(response)
    upsert(data)

if __name__ == "__main__":
    main()