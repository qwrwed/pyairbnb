import json
from argparse import ArgumentParser, Namespace
from urllib.parse import parse_qs, urlparse

from pyairbnb.api import Api
from pyairbnb.start import get_details, search_all
from pyairbnb.utils import parse_proxy


def test0():
    room_id = 668146487515150072
    currency = "MXN"
    check_in = "2024-11-04"
    check_out = "2024-11-10"
    data = get_details(
        room_id=room_id,
        currency=currency,
        check_in=check_in,
        check_out=check_out,
    )
    with open("details0.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def test1():
    room_id = 668146487515150072
    currency = "MXN"
    check_in = "2024-11-02"
    check_out = "2024-11-10"
    proxy_url = parse_proxy("[IP or domain]", "[port]", "[user name]", "[password]")
    data = get_details(
        room_id=room_id,
        currency=currency,
        check_in=check_in,
        check_out=check_out,
        proxy_url=proxy_url,
    )
    with open("details1.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def test11():
    room_url = "https://www.airbnb.com/rooms/762251620189545147"
    currency = "MXN"
    check_in = "2024-11-02"
    check_out = "2024-11-10"
    data = get_details(
        room_url=room_url,
        currency=currency,
        check_in=check_in,
        check_out=check_out,
    )
    with open("details11.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def test2():
    currency = "MXN"
    check_in = "2024-11-04"
    check_out = "2024-11-10"
    ne_lat = -1.03866277790021
    ne_long = -77.53091734683608
    sw_lat = -1.1225978433925647
    sw_long = -77.59713412765507
    zoom_value = 2
    results = search_all(
        check_in,
        check_out,
        ne_lat,
        ne_long,
        sw_lat,
        sw_long,
        zoom_value,
        currency,
        proxy_url="",
    )
    with open("search_all.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)


def test3():
    api = Api()
    calendar_data = api.get_calendar("762251620189545147", "")
    with open("calendar_data.json", "w", encoding="utf-8") as f:
        json.dump(calendar_data, f, indent=4)


tests = [test0, test1, test2, test3, test11]


class ProgramArgsNamespace(Namespace):
    test_n: int


def get_args() -> ProgramArgsNamespace:
    parser = ArgumentParser()
    parser.add_argument("-n", "--test-n", choices=range(len(tests)), type=int)
    return parser.parse_args(namespace=ProgramArgsNamespace())


def main() -> None:
    args = get_args()
    tests[args.test_n]()


if __name__ == "__main__":
    main()
