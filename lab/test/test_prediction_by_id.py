import requests
from test.common import BASE, FARM, show

if __name__ == "__main__":
    res = requests.post(BASE + "/predict", json=FARM.model_dump())
    request_id = res.json()["request_id"]
    show(requests.get(BASE + f"/predictions/{request_id}"))
