import requests

from test.common import BASE, show

if __name__ == "__main__":
    params = {"weekday": "monday", "page": 2, "per_page": 5}
    show(requests.get(BASE + "/predictions/by-weekday", params=params))
