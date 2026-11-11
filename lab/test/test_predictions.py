import requests

from test.common import BASE, show

if __name__ == "__main__":
    show(requests.get(BASE + "/predictions", params={"limit": 5}))
