import requests

from test.common import BASE, FARM, show

if __name__ == "__main__":
    req = FARM.model_dump() | {"farm_id": "FARM-999", "region": "New York"}
    show(requests.post(BASE + "/predict", json=req))
