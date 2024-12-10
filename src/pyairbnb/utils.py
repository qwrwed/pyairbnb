import re
from typing import Any
from urllib.parse import quote

from curl_cffi.requests import ProxySpec

regex_space = re.compile(r"[\s ]+")
regx_price = re.compile(r"\d+")


def remove_space(value: str) -> str:
    return regex_space.sub(" ", value.strip())


def get_nested_value(
    d: dict,
    key_path: str,
    default: Any = None,
) -> Any:
    keys = key_path.split(".")
    current = d
    for key in keys:
        current = current.get(key, {})
        if current == {} or current is None:
            return default
    return current


def parse_price_symbol(price_raw: str) -> tuple[float, str]:
    price_raw = price_raw.replace(",", "")

    price_number_match = regx_price.search(price_raw)

    if price_number_match is None:
        return 0, ""

    price_number = price_number_match.group(0)

    price_currency = (
        price_raw.replace(price_number, "").replace(" ", "").replace("-", "")
    )

    price_converted = float(price_number)
    if price_raw.startswith("-"):
        price_converted *= -1

    return price_converted, price_currency


def parse_proxy(ip_or_domain: str, port: str, username: str, password: str) -> str:
    encoded_username = quote(username)
    encoded_password = quote(password)
    proxy_url = f"http://{encoded_username}:{encoded_password}@{ip_or_domain}:{port}"
    return proxy_url


def make_html_headers(
    api_key: str | None = None,
    connection_close: bool = False,
) -> dict[str, str]:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    if connection_close:
        headers["Connection"] = "close"

    if api_key:
        headers["X-Airbnb-Api-Key"] = api_key
    return headers


def make_json_headers(api_key: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Airbnb-Api-Key": api_key,
    }


def make_proxies(proxy_url: str | None = None) -> ProxySpec:
    if proxy_url:
        return {"http": proxy_url, "https": proxy_url}
    return {}
