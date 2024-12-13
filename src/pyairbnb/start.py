from http.cookiejar import reach  # type: ignore[attr-defined]
from urllib.parse import urlparse

from curl_cffi.requests.cookies import Cookies

from pyairbnb import standardize
from pyairbnb.api import Api


def get_details(
    currency: str,
    room_url: str | None = None,
    room_id: str | None = None,
    domain: str = "www.airbnb.com",
    check_in: str | None = None,
    check_out: str | None = None,
    proxy_url: str | None = None,
) -> dict:
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
    if room_url is None and room_id is None:
        raise ValueError("Either room_url or room_id must be provided.")

    _room_url = room_url or f"https://{domain}/rooms/{room_id}"
    _room_id = room_id or urlparse(_room_url).path.split("/")[-1]

    api = Api(
        currency=currency,
        proxy_url=proxy_url,
    )
    data, price_input, cookies = api.get_details(_room_url)
    cookies = Cookies(cookies.get_dict(domain=reach(domain)))

    product_id = price_input["product_id"]

    # Get calendar and reviews data
    data["calendar"] = api.get_calendar(_room_id)
    data["reviews"] = api.get_reviews(product_id)

    # Get price data if check-in and check-out dates are provided
    if check_in and check_out:
        price_data = api.get_price(
            product_id,
            price_input["impression_id"],
            cookies,
            check_in,
            check_out,
        )
        data["price"] = price_data

    # Get host details
    host_id = data["host"]["id"]
    data["host_details"] = api.get_host_details(host_id, cookies)

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
) -> list:
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
    api = Api(
        currency=currency,
        proxy_url=proxy_url,
    )

    all_results = []
    cursor = ""
    while True:
        results_raw = api.get_search(
            check_in,
            check_out,
            ne_lat,
            ne_long,
            sw_lat,
            sw_long,
            zoom_value,
            cursor,
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
) -> list:
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
    api = Api(
        currency=currency,
        proxy_url=proxy_url,
    )

    results_raw = api.get_search(
        check_in,
        check_out,
        ne_lat,
        ne_long,
        sw_lat,
        sw_long,
        zoom_value,
    )

    return standardize.from_search(results_raw)
