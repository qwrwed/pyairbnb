
import pyairbnb.details as details
import pyairbnb.reviews as reviews
import pyairbnb.price as price
import pyairbnb.api as api
import pyairbnb.search as search
import pyairbnb.standardize as standardize
import pyairbnb.calendar as calendar
from datetime import datetime
from urllib.parse import urlparse, parse_qs

def search_all(check_in:str, check_out:str, ne_lat:float, ne_long:float, sw_lat:float, sw_long:float, zoom_value:int, currency:str, proxy_url:str):
    api_key = api.get(proxy_url)
    all_results = []
    cursor = ""
    while True:
        results_raw = search.get(check_in,check_out,ne_lat,ne_long,sw_lat,sw_long,zoom_value,cursor, currency, api_key, proxy_url)
        results = standardize.from_search(results_raw.get("searchResults",[]))
        all_results = all_results + results
        if len(results)==0 or "nextPageCursor" not in results_raw["paginationInfo"] or  results_raw["paginationInfo"]["nextPageCursor"] is None:
            break
        cursor = results_raw["paginationInfo"]["nextPageCursor"]
    return all_results

def search_first_page(check_in:str, check_out:str, ne_lat:float, ne_long:float, sw_lat:float, sw_long:float, zoom_value:int, cursor:str, currency:str, proxy_url:str):
    api_key = api.get(proxy_url)
    results = search.get(check_in,check_out,ne_lat,ne_long,sw_lat,sw_long,zoom_value,"", currency, api_key, proxy_url)
    results = standardize.from_search(results)
    return results

def get_reviews(room_url: str, proxy_url: str):
    data, price_input, cookies = details.get(room_url, proxy_url)#in order not to waste data from this request, I return also this metadata
    product_id = price_input["product_id"]
    api_key = price_input["api_key"]
    reviews_data = reviews.get(product_id,api_key,proxy_url)
    data["reviews"] = reviews_data
    return data

def get_calendar(room_url: str, proxy_url: str):
    data, price_input, cookies = details.get(room_url, proxy_url)#in order not to waste data from this request, I return also this metadata
    api_key = price_input["api_key"]

    parsed_url = urlparse(room_url)
    path = parsed_url.path
    splited = path.split("/")
    room_id = splited[len(splited)-1]

    current_month = datetime.now().month
    current_year = datetime.now().year
    calendar_data = calendar.get(room_id,current_month,current_year,api_key,proxy_url)
    data["calendar"] = calendar_data
    return data

def get_details_from_url(room_url: str, currency: str, check_in: str, check_out: str, proxy_url: str):
    data, price_input, cookies = details.get(room_url, proxy_url)
    product_id = price_input["product_id"]
    api_key = price_input["api_key"]
    
    parsed_url = urlparse(room_url)
    path = parsed_url.path
    splited = path.split("/")
    room_id = splited[len(splited)-1]

    current_month = datetime.now().month
    current_year = datetime.now().year
    calendar_data = calendar.get(room_id,current_month,current_year,api_key,proxy_url)
    data["calendar"] = calendar_data

    reviews_data = reviews.get(product_id,api_key,proxy_url)
    data["reviews"] = reviews_data
    if check_in is None or check_in == "" or check_out is None or check_out == "":
        return data
    price_data = price.get(product_id,price_input["impression_id"],api_key,currency, cookies, check_in, check_out, proxy_url)
    data["price"] = price_data
    return data

def get_details_from_id(room_id: int, currency: str, check_in: str, check_out: str, proxy_url: str):
    room_url = f"https://www.airbnb.com/rooms/{room_id}"
    data, price_input, cookies = details.get(room_url, proxy_url)
    product_id = price_input["product_id"]
    api_key = price_input["api_key"]

    current_month = datetime.now().month
    current_year = datetime.now().year
    calendar_data = calendar.get(room_id,current_month,current_year,api_key,proxy_url)
    data["calendar"] = calendar_data

    reviews_data = reviews.get(product_id,api_key,proxy_url)
    data["reviews"] = reviews_data
    if check_in is None or check_in == "" or check_out is None or check_out == "":
        return data
    price_data = price.get(product_id,price_input["impression_id"],api_key,currency, cookies, check_in, check_out, proxy_url)
    data["price"] = price_data
    return data


def get_details_from_id_and_domain(room_id: int, domain: str, currency: str, check_in: str, check_out: str, proxy_url: str):
    room_url = f"https://{domain}/rooms/{room_id}"
    data, price_input, cookies = details.get(room_url, proxy_url)
    product_id = price_input["product_id"]
    api_key = price_input["api_key"]
    current_month = datetime.now().month
    current_year = datetime.now().year
    calendar_data = calendar.get(room_id,current_month,current_year,api_key,proxy_url)
    data["calendar"] = calendar_data
    reviews_data = reviews.get(product_id,api_key,proxy_url)
    data["reviews"] = reviews_data
    if check_in is None or check_in == "" or check_out is None or check_out == "":
        return data
    price_data = price.get(product_id,price_input["impression_id"],api_key,currency, cookies, check_in, check_out, proxy_url)
    data["price"] = price_data
    return data