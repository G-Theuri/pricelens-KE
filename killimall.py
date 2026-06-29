from curl_cffi import requests as cureq
from rich import print
import json

response =  cureq.get("https://mall-api.kilimall.com/search?skip=0&size=50&frontCategoryId=872&useSuggestion=true&limit=36",
                      impersonate='chrome')

listings = response.json().get("data").get("result")

for listing in listings:
    info = {

        "SKU": listing.get("defaultSkuId"),
        "URl": "https://www.kilimall.co.ke/listing/" + str(listing.get("listingId")),
        "IMG": listing.get("image"),
        "Price": listing.get("price"),
    }
    print(json.dumps(info, indent=4))