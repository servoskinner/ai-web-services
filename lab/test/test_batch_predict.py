import requests

from test.common import BASE, FARM, show

if __name__ == "__main__":
    items = [FARM.model_dump() | {"farm_id": f"FARM-00{i}"} for i in range(1, 4)]
    show(requests.post(BASE + "/batch-predict", json={"items": items}))
