import requests

from test.common import BASE, show

if __name__ == "__main__":
    show(requests.post(BASE + "/demo/seed-weekdays", params={"count": 70}))
