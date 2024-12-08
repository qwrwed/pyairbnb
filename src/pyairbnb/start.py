from datetime import datetime
from urllib.parse import urlparse

import pyairbnb.api as api
import pyairbnb.calendar as calendar
import pyairbnb.details as details
import pyairbnb.host_details as host_details
import pyairbnb.price as price
import pyairbnb.reviews as reviews
import pyairbnb.search as search
import pyairbnb.standardize as standardize


def get_calendar(
    room_id: str,
    api_key: str = "",
    proxy_url: str | None = None,
):
    """
    Retrieves the calendar data for a specified room.

    Args:
        room_id (str): The room ID.
        api_key (str): The API key.
        proxy_url (str): The proxy URL.

    Returns:
        dict: Calendar data.
    """
    if not api_key:
        api_key = api.get(proxy_url)

    current_month = datetime.now().month
    current_year = datetime.now().year
    return calendar.get(room_id, current_month, current_year, api_key, proxy_url)


def get_reviews(
    product_id: str,
    api_key: str = "",
    proxy_url: str | None = None,
):
    """
    Retrieves review data for a specified product.

    Args:
        product_id (str): The product ID.
        api_key (str): The API key.
        proxy_url (str): The proxy URL.

    Returns:
        dict: Reviews data.
    """
    if not api_key:
        api_key = api.get(proxy_url)

    return reviews.get(product_id, api_key, proxy_url)


def get_details(
    room_url: str = None,
    room_id: int = None,
    domain: str = "www.airbnb.com",
    currency: str = None,
    check_in: str = None,
    check_out: str = None,
    proxy_url: str | None = None,
):
    """
    Retrieves all details (calendar, reviews, price, and host details) for a specified room.

    Args:
        room_url (str): The room URL (optional if room_id is provided).
        room_id (int): The room ID (optional if room_url is provided).
        domain (str): The domain (default is 'www.airbnb.com').
        currency (str): Currency for pricing information.
        check_in (str): Check-in date for price information.
        check_out (str): Check-out date for price information.
        proxy_url (str): Proxy URL.

    Returns:
        dict: A dictionary with all room details.
    """
    if not room_url and room_id is None:
        raise ValueError("Either room_url or room_id must be provided.")

    if not room_url:
        room_url = f"https://{domain}/rooms/{room_id}"

    data, price_input, cookies = details.get(room_url, proxy_url)
    product_id = price_input["product_id"]
    api_key = price_input["api_key"]

    # Extract room_id from URL if not provided
    if room_id is None:
        parsed_url = urlparse(room_url)
        path = parsed_url.path
        room_id = path.split("/")[-1]

    # Get calendar and reviews data
    data["calendar"] = get_calendar(room_id, api_key, proxy_url)
    data["reviews"] = get_reviews(product_id, api_key, proxy_url)

    # Get price data if check-in and check-out dates are provided
    if check_in and check_out:
        price_data = price.get(
            product_id,
            price_input["impression_id"],
            api_key,
            currency,
            cookies,
            check_in,
            check_out,
            proxy_url,
        )
        data["price"] = price_data

    # Get host details
    host_id = data["host"]["id"]
    data["host_details"] = host_details.get(host_id, api_key, proxy_url, cookies)

    return data


def search_all(
    check_in: str,
    check_out: str,
    ne_lat: float,
    ne_long: float,
    sw_lat: float,
    sw_long: float,
    zoom_value: int,
    currency: str,
    proxy_url: str | None = None,
):
    """
    Performs a paginated search for all rooms within specified geographic bounds.

    Args:
        check_in (str): Check-in date.
        check_out (str): Check-out date.
        ne_lat (float): Latitude of northeast corner.
        ne_long (float): Longitude of northeast corner.
        sw_lat (float): Latitude of southwest corner.
        sw_long (float): Longitude of southwest corner.
        zoom_value (int): Zoom level.
        currency (str): Currency for pricing information.
        proxy_url (str): Proxy URL.

    Returns:
        list: A list of all search results.
    """
    api_key = api.get(proxy_url)
    all_results = []
    cursor = ""
    while True:
        results_raw = search.get(
            check_in,
            check_out,
            ne_lat,
            ne_long,
            sw_lat,
            sw_long,
            zoom_value,
            cursor,
            currency,
            api_key,
            proxy_url,
        )
        results = standardize.from_search(results_raw.get("searchResults", []))
        all_results.extend(results)
        if (
            not results
            or "nextPageCursor" not in results_raw["paginationInfo"]
            or results_raw["paginationInfo"]["nextPageCursor"] is None
        ):
            break
        cursor = results_raw["paginationInfo"]["nextPageCursor"]
    return all_results


def search_first_page(
    check_in: str,
    check_out: str,
    ne_lat: float,
    ne_long: float,
    sw_lat: float,
    sw_long: float,
    zoom_value: int,
    currency: str,
    proxy_url: str | None = None,
):
    """
    Searches the first page of results within specified geographic bounds.

    Args:
        check_in (str): Check-in date.
        check_out (str): Check-out date.
        ne_lat (float): Latitude of northeast corner.
        ne_long (float): Longitude of northeast corner.
        sw_lat (float): Latitude of southwest corner.
        sw_long (float): Longitude of southwest corner.
        zoom_value (int): Zoom level.
        currency (str): Currency for pricing information.
        proxy_url (str): Proxy URL.

    Returns:
        list: A list of search results from the first page.
    """
    api_key = api.get(proxy_url)
    results_raw = search.get(
        check_in,
        check_out,
        ne_lat,
        ne_long,
        sw_lat,
        sw_long,
        zoom_value,
        "",
        currency,
        api_key,
        proxy_url,
    )
    return standardize.from_search(results_raw)
