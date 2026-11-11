import requests

from test.common import BASE, show

if __name__ == "__main__":
    show(requests.get(BASE + "/predictions/00000000-0000-0000-0000-000000000000"))
