import json
import re
from typing import Any

from bs4 import BeautifulSoup

from pyairbnb import standardize, utils

regexApiKey = re.compile(r'"key":".+?"')
regexLanguage = re.compile(r'"language":".+?"')


def parse_body_details_wrapper(body: str):
    data_raw, language, api_key = parse_body_details(body)
    data_formatted = standardize.from_details(data_raw)
    data_formatted["language"] = language
    price_dependency_input = {
        "product_id": data_raw["variables"]["id"],
        "impression_id": data_raw["variables"]["pdpSectionsRequest"]["p3ImpressionId"],
        "api_key": api_key,
    }
    return data_formatted, price_dependency_input


def parse_body_details(body: str) -> tuple[Any, str, str]:
    soup = BeautifulSoup(body, "html.parser")
    data_deferred_state = soup.select("#data-deferred-state-0")[0].getText()
    html_data = utils.remove_space(data_deferred_state)

    language_match = regexLanguage.search(body)
    if not language_match:
        raise AttributeError("could not extract language from response text")
    language = language_match.group()
    language = language.replace('"language":"', "")
    language = language.replace('"', "")

    api_key_match = regexApiKey.search(body)
    if not api_key_match:
        raise AttributeError("could not extract API key from response text")
    api_key = api_key_match.group()
    api_key = api_key.replace('"key":"', "")
    api_key = api_key.replace('"', "")

    data = json.loads(html_data)
    details_data = data["niobeMinimalClientData"][0][1]
    return details_data, language, api_key
