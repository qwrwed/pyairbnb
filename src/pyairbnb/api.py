import base64
import json
import re
from datetime import datetime
from functools import cached_property
from typing import Any
from urllib.parse import urlencode

from curl_cffi import requests
from curl_cffi.requests import BrowserTypeLiteral, Cookies, Response

from pyairbnb import parse
from pyairbnb.utils import (
    get_nested_value,
    make_html_headers,
    make_json_headers,
    make_proxies,
)


class Api:
    def __init__(
        self,
        proxy_url: str | None = None,
        timeout_get: int = 60,
    ):
        self.proxies = make_proxies(proxy_url)
        self.timeout_get = timeout_get

    @property
    def json_headers(self) -> dict[str, str]:
        return make_json_headers(self.api_key)

    def get(
        self,
        url: str,
        headers: dict[str, str],
        params: dict | list | tuple | None = None,
        cookies: Cookies | None = None,
    ) -> Response:
        return requests.get(
            url=url,
            params=params,
            headers=headers,
            proxies=self.proxies,
            cookies=cookies,
            timeout=self.timeout_get,
        )

    def get_json(
        self,
        url: str,
        params: dict | list | tuple | None = None,
        headers: dict[str, str] | None = None,
        cookies: Cookies | None = None,
    ):
        if headers is None:
            headers = self.json_headers

        response = self.get(
            url=url,
            headers=headers,
            params=params,
            cookies=cookies,
        )
        response.raise_for_status()
        data = response.json()
        return data

    def get_html(
        self,
        url: str,
        use_api_key: bool,
        header_connection_close: bool,
        params: dict | list | tuple | None = None,
    ) -> Response:
        headers = make_html_headers(
            api_key=self.api_key if use_api_key else None,
            connection_close=header_connection_close,
        )
        return self.get(
            url=url,
            headers=headers,
            params=params,
        )

    def post(
        self,
        url: str,
        params: dict[str, Any],
        json_data: dict[str, Any],
        headers: dict[str, str],
        impersonate: BrowserTypeLiteral = "chrome110",
    ) -> Response:
        url_parsed = f"{url}?{urlencode(params)}"
        return requests.post(
            url=url_parsed,
            json=json_data,
            headers=headers,
            proxies=self.proxies,
            impersonate=impersonate,
        )

    @cached_property
    def api_key(self) -> str:
        response: Response = self.get_html(
            url="https://www.airbnb.com",
            use_api_key=False,
            header_connection_close=False,
        )
        response.raise_for_status()
        body = response.text
        match = re.search(r'"api_config":{"key":"(.+?)"', body)
        if not match:
            raise AttributeError("could not extract API key from response text")
        api_key = match.group(1)
        return api_key

    def get_details(
        self,
        room_url: str,
    ) -> tuple[dict[str, Any], dict[str, Any], Cookies]:
        response: Response = self.get_html(
            url=room_url,
            use_api_key=False,
            header_connection_close=False,
        )
        response.raise_for_status()

        data_formatted, price_dependency_input = parse.parse_body_details_wrapper(
            response.text
        )
        cookies = response.cookies

        return data_formatted, price_dependency_input, cookies

    def get_calendar(
        self,
        room_id: str,
        month: int | None = None,
        year: int | None = None,
        currency: str = "USD",
    ):
        month = month or datetime.now().month
        year = year or datetime.now().year
        endpoint = "https://www.airbnb.com/api/v3/PdpAvailabilityCalendar/8f08e03c7bd16fcad3c92a3592c19a8b559a0d0855a84028d1163d4733ed9ade/"
        variables_data = {
            "request": {
                "count": 12,
                "listingId": room_id,
                "month": month,
                "year": year,
            },
        }
        extension = {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "8f08e03c7bd16fcad3c92a3592c19a8b559a0d0855a84028d1163d4733ed9ade",
            },
        }
        data_raw_extension = json.dumps(extension)
        data_raw_variables = json.dumps(variables_data)
        query = {
            "operationName": "PdpAvailabilityCalendar",
            "locale": "en",
            "currency": currency,
            "variables": data_raw_variables,
            "extensions": data_raw_extension,
        }
        url = f"{endpoint}?{urlencode(query)}"

        data = self.get_json(url)
        calendar = get_nested_value(
            data,
            key_path="data.merlin.pdpAvailabilityCalendar.calendarMonths",
            default=[],
        )
        return calendar

    def get_reviews(
        self,
        product_id: str,
    ) -> list:
        offset = 0
        all_reviews: list = []
        while True:
            reviews = self._get_reviews_from_offset(offset, product_id)
            offset = offset + 50
            if len(reviews) == 0:
                break
            all_reviews.extend(reviews)
        return all_reviews

    def _get_reviews_from_offset(
        self,
        offset: int,
        product_id: str,
    ) -> str:
        endpoint = "https://www.airbnb.com/api/v3/StaysPdpReviewsQuery/dec1c8061483e78373602047450322fd474e79ba9afa8d3dbbc27f504030f91d/"
        variables_data = {
            "id": product_id,
            "pdpReviewsRequest": {
                "fieldSelector": "for_p3_translation_only",
                "forPreview": False,
                "limit": 50,
                "offset": f"{offset}",
                "showingTranslationButton": False,
                "first": 50,
                "sortingPreference": "MOST_RECENT",
                "numberOfAdults": "1",
                "numberOfChildren": "0",
                "numberOfInfants": "0",
                "numberOfPets": "0",
                "after": None,
            },
        }
        entension = {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "dec1c8061483e78373602047450322fd474e79ba9afa8d3dbbc27f504030f91d",
            },
        }
        data_raw_extension = json.dumps(entension)
        data_raw_variables = json.dumps(variables_data)
        query = {
            "operationName": "StaysPdpReviewsQuery",
            "locale": "en",
            "currency": "USD",
            "variables": data_raw_variables,
            "extensions": data_raw_extension,
        }
        url = f"{endpoint}?{urlencode(query)}"

        data = self.get_json(url)

        reviews = get_nested_value(
            data,
            key_path="data.presentation.stayProductDetailPage.reviews.reviews",
            default={},
        )
        return reviews

    def get_host_details(
        self,
        host_id: str,
        cookies: Cookies,
    ):
        # Encode the host ID to match Airbnb's required format
        host_id = "User:" + host_id
        user_id = base64.b64encode(host_id.encode()).decode("utf-8")

        # Set up parameters
        params = {
            "operationName": "GetUserProfile",
            "locale": "en",
            "currency": "USD",
            "variables": json.dumps(
                {
                    "userId": user_id,
                    "isPassportStampsEnabled": True,
                    "mockIdentifier": None,
                    "fetchCombinedSportsAndInterests": True,
                }
            ),
            "extensions": json.dumps(
                {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "a56d8909f271740ccfef23dd6c34d098f194f4a6e7157f244814c5610b8ad76a",
                    }
                }
            ),
        }

        data = self.get_json(
            url="https://www.airbnb.com/api/v3/GetUserProfile/a56d8909f271740ccfef23dd6c34d098f194f4a6e7157f244814c5610b8ad76a",
            params=params,
            cookies=cookies,
        )

        return data

    def get_search(
        self,
        check_in: str,
        check_out: str,
        ne_lat: float,
        ne_long: float,
        sw_lat: float,
        sw_long: float,
        zoom_value: int,
        cursor: str,
        currency: str,
    ):
        treatment = [
            "feed_map_decouple_m11_treatment",
            "stays_search_rehydration_treatment_desktop",
            "stays_search_rehydration_treatment_moweb",
            "selective_query_feed_map_homepage_desktop_treatment",
            "selective_query_feed_map_homepage_moweb_treatment",
        ]
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")

        difference = check_out_date - check_in_date

        days = difference.days

        base_url = "https://www.airbnb.com/api/v3/StaysSearch/d4d9503616dc72ab220ed8dcf17f166816dccb2593e7b4625c91c3fce3a3b3d6"
        query_params = {
            "operationName": "StaysSearch",
            "locale": "en",
            "currency": currency,
        }
        url_parsed = f"{base_url}?{urlencode(query_params)}"
        raw_params = [
            {"filterName": "cdnCacheSafe", "filterValues": ["false"]},
            {"filterName": "channel", "filterValues": ["EXPLORE"]},
            {"filterName": "checkin", "filterValues": [check_in]},
            {"filterName": "checkout", "filterValues": [check_out]},
            {"filterName": "datePickerType", "filterValues": ["calendar"]},
            {"filterName": "flexibleTripLengths", "filterValues": ["one_week"]},
            {
                "filterName": "itemsPerGrid",
                "filterValues": ["50"],
            },  # if you read this, this is items returned number, this can bex exploited  ;)
            {"filterName": "monthlyLength", "filterValues": ["3"]},
            {"filterName": "monthlyStartDate", "filterValues": ["2024-02-01"]},
            {"filterName": "neLat", "filterValues": [str(ne_lat)]},
            {"filterName": "neLng", "filterValues": [str(ne_long)]},
            {"filterName": "placeId", "filterValues": ["ChIJpTeBx6wjq5oROJeXkPCSSSo"]},
            {"filterName": "priceFilterInputType", "filterValues": ["0"]},
            {"filterName": "priceFilterNumNights", "filterValues": [str(days)]},
            {"filterName": "query", "filterValues": ["Galapagos Island, Ecuador"]},
            {"filterName": "screenSize", "filterValues": ["large"]},
            {"filterName": "refinementPaths", "filterValues": ["/homes"]},
            {"filterName": "searchByMap", "filterValues": ["true"]},
            {"filterName": "swLat", "filterValues": [str(sw_lat)]},
            {"filterName": "swLng", "filterValues": [str(sw_long)]},
            {"filterName": "tabId", "filterValues": ["home_tab"]},
            {"filterName": "version", "filterValues": ["1.8.3"]},
            {"filterName": "zoomLevel", "filterValues": [str(zoom_value)]},
        ]
        input_data = {
            "operationName": "StaysSearch",
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "d4d9503616dc72ab220ed8dcf17f166816dccb2593e7b4625c91c3fce3a3b3d6",
                },
            },
            "variables": {
                "includeMapResults": True,
                "isLeanTreatment": False,
                "staysMapSearchRequestV2": {
                    "cursor": cursor,
                    "requestedPageType": "STAYS_SEARCH",
                    "metadataOnly": False,
                    "source": "structured_search_input_header",
                    "searchType": "user_map_move",
                    "treatmentFlags": treatment,
                    "rawParams": raw_params,
                },
                "staysSearchRequest": {
                    "cursor": cursor,
                    "maxMapItems": 9999,
                    "requestedPageType": "STAYS_SEARCH",
                    "metadataOnly": False,
                    "source": "structured_search_input_header",
                    "searchType": "user_map_move",
                    "treatmentFlags": treatment,
                    "rawParams": raw_params,
                },
            },
        }

        headers = make_html_headers(
            self.api_key,
            connection_close=True,
        )

        response = requests.post(
            url_parsed,
            json=input_data,
            headers=headers,
            proxies=self.proxies,
            impersonate="chrome110",
        )

        data = response.json()

        to_return = get_nested_value(
            data,
            "data.presentation.staysSearch.results",
            {},
        )

        return to_return

    def get_price(
        self,
        product_id: str,
        impression_id: str,
        currency: str,
        cookies: Cookies,
        check_in: str,
        check_out: str,
    ) -> dict:
        endpoint = "https://www.airbnb.com/api/v3/StaysPdpSections/80c7889b4b0027d99ffea830f6c0d4911a6e863a957cbe1044823f0fc746bf1f"
        extension = {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "80c7889b4b0027d99ffea830f6c0d4911a6e863a957cbe1044823f0fc746bf1f",
            },
        }
        data_raw_extension = json.dumps(extension)
        variables_data = {
            "id": product_id,
            "pdpSectionsRequest": {
                "adults": "1",
                "bypassTargetings": False,
                "categoryTag": None,
                "causeId": None,
                "children": None,
                "disasterId": None,
                "discountedGuestFeeVersion": None,
                "displayExtensions": None,
                "federatedSearchId": None,
                "forceBoostPriorityMessageType": None,
                "infants": None,
                "interactionType": None,
                "layouts": ["SIDEBAR", "SINGLE_COLUMN"],
                "pets": 0,
                "pdpTypeOverride": None,
                "photoId": None,
                "preview": False,
                "previousStateCheckIn": None,
                "previousStateCheckOut": None,
                "priceDropSource": None,
                "privateBooking": False,
                "promotionUuid": None,
                "relaxedAmenityIds": None,
                "searchId": None,
                "selectedCancellationPolicyId": None,
                "selectedRatePlanId": None,
                "splitStays": None,
                "staysBookingMigrationEnabled": False,
                "translateUgc": None,
                "useNewSectionWrapperApi": False,
                "sectionIds": [
                    "BOOK_IT_FLOATING_FOOTER",
                    "POLICIES_DEFAULT",
                    "EDUCATION_FOOTER_BANNER_MODAL",
                    "BOOK_IT_SIDEBAR",
                    "URGENCY_COMMITMENT_SIDEBAR",
                    "BOOK_IT_NAV",
                    "MESSAGE_BANNER",
                    "HIGHLIGHTS_DEFAULT",
                    "EDUCATION_FOOTER_BANNER",
                    "URGENCY_COMMITMENT",
                    "BOOK_IT_CALENDAR_SHEET",
                    "CANCELLATION_POLICY_PICKER_MODAL",
                ],
                "checkIn": check_in,
                "checkOut": check_out,
                "p3ImpressionId": impression_id,
            },
        }
        data_raw_variables = json.dumps(variables_data)
        query = {
            "operationName": "StaysPdpSections",
            "locale": "en",
            "currency": currency,
            "variables": data_raw_variables,
            "extensions": data_raw_extension,
        }
        url = f"{endpoint}?{urlencode(query)}"

        session = requests.Session()

        for name in cookies:
            session.cookies.set(name, cookies[name])

        response = session.get(url, headers=self.json_headers, proxies=self.proxies)

        response.raise_for_status()
        data = response.json()

        sections = get_nested_value(
            data,
            key_path="data.presentation.stayProductDetailPage.sections.sections",
            default={},
        )

        for section in sections:
            if section["sectionId"] == "BOOK_IT_SIDEBAR":
                price_data = get_nested_value(
                    section, "section.structuredDisplayPrice", {}
                )
                final_data = {
                    "main": {
                        "price": get_nested_value(price_data, "primaryLine.price", {}),
                        "discountedPrice": get_nested_value(
                            price_data, "primaryLine.discountedPrice", {}
                        ),
                        "originalPrice": get_nested_value(
                            price_data, "primaryLine.originalPrice", {}
                        ),
                        "qualifier": get_nested_value(
                            price_data, "primaryLine.qualifier", {}
                        ),
                    },
                    "details": {},
                }
                details = get_nested_value(
                    price_data, "explanationData.priceDetails", {}
                )
                for detail in details:
                    for item in get_nested_value(detail, "items", {}):
                        final_data["details"][item["description"]] = item["priceString"]
                return final_data
        return {}
