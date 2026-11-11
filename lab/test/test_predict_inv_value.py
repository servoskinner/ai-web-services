import requests

from test.common import BASE, FARM, show

if __name__ == "__main__":
    req = FARM.model_dump() | {"area_ha": -100}
    show(requests.post(BASE + "/predict", json=req))
